import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
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

# --- your same functions (unchanged) ---
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

        self.sub = self.create_subscription(
            Image,
            '/cam_feed',
            self.callback,
            10
        )

    def callback(self, msg):
        frame = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        frame = cv2.resize(frame, FRAME)

        # --- YOLO ---
        results = yolo_model(frame, verbose=False)[0]
        detections = results.boxes

        # --- MiDaS ---
        depth_input = midas_transform(frame).to(device)

        with torch.no_grad():
            depth_output = midas_model(depth_input)
            depth_map = postprocess_depth(
                depth_output, FRAME[0], FRAME[1]
            )

        # --- normalize ---
        depth_map = normalize_depth_stable(depth_map)

        if USE_INVERTED_DEPTH:
            depth_map = 1.0 - depth_map

        depth_map = smooth_depth(depth_map)

        # --- visualization ---
        vis = frame.copy()

        for box in detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)

        depth_vis = (depth_map * 255).astype(np.uint8)
        depth_vis = cv2.applyColorMap(depth_vis, cv2.COLORMAP_MAGMA)

        combined = np.hstack((vis, depth_vis))

        cv2.imshow("RGB | Depth", combined)
        cv2.waitKey(1)


def main():
    rclpy.init()
    node = VisionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
