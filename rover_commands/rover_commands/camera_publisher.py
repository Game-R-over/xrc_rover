import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess

class CameraPublisherNode(Node):
    def __init__(self):
        super().__init__('camera_publisher')

        self.gst_process = None
        self.current_mode = None
        self.pc_ip = '10.132.166.188'

        self.mode_subscriber = self.create_subscription(
            String,
            '/camera/mode',
            self.callback_mode,
            10
        )

        self.launch('navigation')
        self.get_logger().info('Camera node ready')

    def callback_mode(self, msg):
        if msg.data == self.current_mode:
            return
        self.launch(msg.data)

    def launch(self, mode):
        self.stop()
        
        if mode == 'navigation':
            pipeline = self.navigation_pipeline()
        elif mode == 'autonomy':
            pipeline = self.autonomy_pipeline()
        else:
            self.get_logger().warn(f'Unknown mode: {mode}')
            return
        
        self.gst_process = subprocess.Popen(
            ['gst-launch-1.0'] + pipeline.split(),
            stdout=subprocess.DEVNULL
            # stderr is left un-redirected so it prints to the terminal for debugging!
        )
        
        self.current_mode = mode
        self.get_logger().info(f'Started mode: {mode}')

    def stop(self):
        if self.gst_process is not None:
            self.gst_process.terminate()
            self.gst_process.wait()
            self.gst_process = None

    def navigation_pipeline(self):
        return (
            f'v4l2src device=/dev/video0 ! '
            f'video/x-raw,width=320,height=240,framerate=30/1 ! '
            f'videoconvert ! '
            f'x264enc tune=zerolatency bitrate=500 speed-preset=superfast key-int-max=15 ! ' 
            f'mpegtsmux ! '
            f'udpsink host={self.pc_ip} port=5000'
        )

    def autonomy_pipeline(self):
        return (
            f'v4l2src device=/dev/video0 ! '
            f'video/x-raw,width=1280,height=720,framerate=30/1 ! '
            f'videorate ! '
            f'video/x-raw,framerate=5/1 ! '
            f'videoconvert ! '
            f'x264enc tune=zerolatency bitrate=2000 speed-preset=superfast key-int-max=10 ! '
            f'mpegtsmux ! '
            f'udpsink host={self.pc_ip} port=5000'
        )

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
