import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

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

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        
        self.bridge = CvBridge()
        self.current_mode = None
        
        self.mode_subscriber = self.create_subscription(
            String,
            '/camera/mode',
            self.callback_mode,
            10
        )
        
        self.image_publisher = self.create_publisher(
            Image,
            '/camera/processed_image',
            10
        )
        
        self.start('navigation')

    def callback_mode(self, msg):
        if msg.data != self.current_mode:
            self.start(msg.data)

    def start(self, mode):
        self.stop()
        self.current_mode = mode
        
        pipeline = (
            'udpsrc port=5000 '
            'caps="application/x-rtp,media=video,clock-rate=90000,encoding-name=H264" ! '
            'rtph264depay ! avdec_h264 ! videoconvert ! '
            'video/x-raw,format=BGR ! '
            'appsink drop=1 max-buffers=1 sync=false'
        )
        
        self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        
        fps = 30 if mode == 'navigation' else 5
        period = 1.0 / fps
        self.timer = self.create_timer(period, self.read_frame)

    def read_frame(self):
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return

        encoding = 'mono8' if self.current_mode == 'navigation' else 'bgr8'
        if encoding == 'mono8':
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            msg = self.bridge.cv2_to_imgmsg(gray_frame, encoding=encoding)
        else:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding=encoding)
        self.image_publisher.publish(msg)
        
        frame_resized = cv2.resize(frame, FRAME)
        
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

        # Visualization
        vis = frame_resized.copy()
        for box in detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)

        depth_vis = (depth_map * 255).astype(np.uint8)
        depth_vis = cv2.applyColorMap(depth_vis, cv2.COLORMAP_MAGMA)

        combined = np.hstack((vis, depth_vis))

        cv2.imshow("RGB | Depth", combined)
        cv2.waitKey(1)

    def stop(self):
        if hasattr(self, 'timer'):
            self.timer.cancel()
        if hasattr(self, 'cap'):
            self.cap.release()
            
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
