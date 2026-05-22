import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import CompressedImage
import cv2
from cv_bridge import CvBridge

class CameraPublisherNode(Node):
    def __init__(self):
        super().__init__('camera_publisher')

        self.cap = None
        self.timer = None
        self.current_mode = None
        self.bridge = CvBridge()

        self.mode_subscriber = self.create_subscription(
            String,
            '/camera/mode',
            self.callback_mode,
            10
        )
        
        # Publish using standard ROS 2 CompressedImage
        self.image_publisher = self.create_publisher(
            CompressedImage,
            '/camera/image_raw/compressed',
            10
        )

        self.launch('navigation')
        self.get_logger().info('Camera node ready (ROS 2 Native)')

    def callback_mode(self, msg):
        if msg.data == self.current_mode:
            return
        self.launch(msg.data)

    def launch(self, mode):
        self.stop()
        
        self.cap = cv2.VideoCapture(0)
        
        if mode == 'navigation':
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            fps = 30
        elif mode == 'autonomy':
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 5)
            fps = 5
        else:
            self.get_logger().warn(f'Unknown mode: {mode}')
            return
            
        self.current_mode = mode
        self.timer = self.create_timer(1.0 / fps, self.timer_callback)
        self.get_logger().info(f'Started mode: {mode} at {fps} FPS')

    def timer_callback(self):
        if not self.cap or not self.cap.isOpened():
            return
            
        ret, frame = self.cap.read()
        if ret:
            # Compress natively to reduce Wi-Fi bandwidth
            # Use lower quality for navigation (high FPS), higher for autonomy (low FPS)
            quality = 60 if self.current_mode == 'navigation' else 80
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            
            _, jpeg_data = cv2.imencode('.jpg', frame, encode_param)
            
            # Manually construct CompressedImage to avoid cv_bridge overhead
            msg = CompressedImage()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.format = "jpeg"
            msg.data = jpeg_data.tobytes()
            
            self.image_publisher.publish(msg)

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def destroy_node(self):
        self.stop()
        super().destroy_node()

def main():
    rclpy.init()
    node = CameraPublisherNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
