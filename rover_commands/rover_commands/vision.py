import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage, PointCloud2, PointField
from std_msgs.msg import String
from cv_bridge import CvBridge
from rclpy.qos import qos_profile_sensor_data

import cv2
import torch
import numpy as np
from ultralytics import YOLO

FRAME = (320, 240)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL_TYPE = "MiDaS_small"

def load_midas_model(device):
    """
    Load MiDaS model and preprocessing transforms.
    """

    midas_model = torch.hub.load("intel-isl/MiDaS", MODEL_TYPE)
    midas_model.to(device)
    midas_model.eval()
    transform = torch.hub.load("intel-isl/MiDaS", "transforms").small_transform
    
    return midas_model, transform

def postprocess_depth(depth_output, width, height):
    """
    Convert MiDaS output tensor to depth map scaled to original frame size.
    """

    depth = depth_output.squeeze().cpu().numpy()
    
    # Resize to match camera frame
    depth_resized = cv2.resize(depth, (width, height), interpolation = cv2.INTER_CUBIC)

    return depth_resized

yolo_model = YOLO("yolov8n.pt")
midas_model, midas_transform = load_midas_model(device)

bridge = CvBridge()

prev_depth = None
running_min = None
running_max = None
SMOOTHING_ALPHA = 0.2
USE_INVERTED_DEPTH = True

def normalize_depth_stable(depth):
    global running_min, running_max

    dmin = depth.min()
    dmax = depth.max()

    if running_min is None:
        running_min = dmin
        running_max = dmax
    else:
        running_min = 0.9 * running_min + 0.1 * dmin
        running_max = 0.9 * running_max + 0.1 * dmax

    depth = (depth - running_min) / (running_max - running_min + 1e-6)
    return np.clip(depth, 0, 1)

def smooth_depth(depth):
    global prev_depth
    if prev_depth is None:
        prev_depth = depth
        return depth
    prev_depth = (1 - SMOOTHING_ALPHA) * prev_depth + SMOOTHING_ALPHA * depth
    return prev_depth

import threading

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        
        self.bridge = CvBridge()
        self.current_mode = None
        self.running = False
        self.latest_frame = None
        
        self.mode_subscriber = self.create_subscription(
            String,
            '/camera/mode',
            self.callback_mode,
            10
        )
        
        # Native zero-latency subscriber
        self.image_subscriber = self.create_subscription(
            CompressedImage,
            '/camera/image_raw/compressed',
            self.callback_image,
            qos_profile_sensor_data
        )
        
        self.image_publisher = self.create_publisher(
            Image,
            '/camera/processed_image',
            10
        )
        
        self.pc_publisher = self.create_publisher(
            PointCloud2,
            '/camera/depth/color/points',
            10
        )
        
        self.start('navigation')

    def callback_image(self, msg):
        # Decode the JPEG natively
        np_arr = np.frombuffer(msg.data, np.uint8)
        self.latest_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    def callback_mode(self, msg):
        if msg.data != self.current_mode:
            self.start(msg.data)

    def start(self, mode):
        import time
        self.stop()
        self.current_mode = mode
        self.running = True
        self.latest_frame = None
        self.last_time = time.time()
        self.fps = 0.0
        
        self.get_logger().info(f'Réception démarrée via ROS 2 CompressedImage : {mode}')
        
        fps_target = 30 if mode == 'navigation' else 5
        period = 1.0 / fps_target
        self.timer = self.create_timer(period, self.process_frame)

    def process_frame(self):
        import time
        current_time = time.time()
        time_diff = current_time - self.last_time
        if time_diff > 0:
            self.fps = (self.fps * 0.9) + ((1.0 / time_diff) * 0.1)  # Smooth FPS
        self.last_time = current_time
        
        if self.latest_frame is None:
            self.get_logger().warn("Waiting for stream... (Make sure camera_publisher.py is running on the Pi!)")
            return
            
        frame = self.latest_frame.copy()

        encoding = 'mono8' if self.current_mode == 'navigation' else 'bgr8'
        if encoding == 'mono8':
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            msg = self.bridge.cv2_to_imgmsg(gray_frame, encoding=encoding)
        else:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding=encoding)
        self.image_publisher.publish(msg)
        
        frame_resized = cv2.resize(frame, FRAME)
        
        if self.current_mode == 'autonomy':
            # --- Autonomy Mode: Heavy AI Processing ---
            
            # YOLO
            results = yolo_model(frame_resized, verbose=False)[0]
            detections = results.boxes

            # MiDaS
            depth_input = midas_transform(frame_resized).to(device)

            with torch.no_grad():
                depth_output = midas_model(depth_input)
                depth_map = postprocess_depth(depth_output, FRAME[0], FRAME[1])

            # Normalize & Smooth Depth
            depth_map = normalize_depth_stable(depth_map)
            if USE_INVERTED_DEPTH:
                depth_map = 1.0 - depth_map
            depth_map = smooth_depth(depth_map)

            # --- Nav2 Perception Bridge: MiDaS to PointCloud2 ---
            MAX_DEPTH = 5.0 # meters (heuristic maximum range)
            metric_depth = depth_map * MAX_DEPTH
            
            # Intrinsics approximation
            width, height = FRAME[0], FRAME[1]
            cx, cy = width / 2.0, height / 2.0
            fx = width * 0.8
            fy = width * 0.8
            
            # Vectorized projection
            u, v = np.meshgrid(np.arange(width), np.arange(height))
            Z = metric_depth
            X = (u - cx) * Z / fx
            Y = (v - cy) * Z / fy
            
            # Filter obstacles (Remove ground and sky)
            mask = (Y < 0.15) & (Z > 0.3) & (Z < 4.5)
            
            pts = np.stack((X[mask], Y[mask], Z[mask]), axis=-1)
            
            # Convert to ROS camera_link conventions (X forward, Y left, Z up)
            if len(pts) > 0:
                ros_pts = np.empty_like(pts, dtype=np.float32)
                ros_pts[:, 0] = pts[:, 2]   # x = Z
                ros_pts[:, 1] = -pts[:, 0]  # y = -X
                ros_pts[:, 2] = -pts[:, 1]  # z = -Y
                
                # Create PointCloud2 msg
                pc_msg = PointCloud2()
                if hasattr(self, 'last_msg_stamp'):
                    pc_msg.header.stamp = self.last_msg_stamp
                else:
                    pc_msg.header.stamp = self.get_clock().now().to_msg()
                pc_msg.header.frame_id = "camera_link"
                pc_msg.height = 1
                pc_msg.width = len(ros_pts)
                pc_msg.is_dense = False
                pc_msg.is_bigendian = False
                
                pc_msg.fields = [
                    PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
                    PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
                    PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1)
                ]
                pc_msg.point_step = 12
                pc_msg.row_step = 12 * len(ros_pts)
                pc_msg.data = ros_pts.tobytes()
                
                self.pc_publisher.publish(pc_msg)

            # Visualization
            vis = frame_resized.copy()
            for box in detections:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)

            depth_vis = (depth_map * 255).astype(np.uint8)
            depth_vis = cv2.applyColorMap(depth_vis, cv2.COLORMAP_MAGMA)

            combined = np.hstack((vis, depth_vis))
            
        else:
            # --- Navigation Mode: Lightweight ---
            combined = frame_resized.copy()
            
        # Draw FPS Counter
        fps_text = f"FPS: {int(self.fps)}"
        cv2.putText(combined, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Rover Feed", combined)
        cv2.waitKey(1)

    def stop(self):
        self.running = False
        if hasattr(self, 'timer') and self.timer is not None:
            self.timer.cancel()
            
    def destroy_node(self):
        self.stop()
        super().destroy_node()

def main():
    rclpy.init()
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
