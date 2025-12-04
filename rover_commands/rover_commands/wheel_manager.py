import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData
from .utils.esp import SerialBridge

class WheelManager(Node):

    subscription = None
    deltadata = {}
    serial_bridge = None

    def __init__(self):
        super().__init__('wheel_manager')

        self.subscription = self.create_subscription(
            MoveData,
            'wheel_update',
            self.listener_callback,
            10
        )

        self.serial_bridge = SerialBridge(self.get_logger)
        self.deltadata= {}

        self.get_logger().info('Wheel Manager node has been started.')


    def listener_callback(self, msg):
        self.get_logger().info('Response')
        self.deltadata['speed'] = msg.speed
        self.deltadata['angle'] = msg.angle

        self.send_to_esp(msg)

        self.get_logger().info(f'Received command: deltaspeed={msg.speed}, deltaangle={msg.angle}')

    def send_to_esp(self, info_to_send):
        self.serial_bridge.send_motor(info_to_send.speed)
        self.serial_bridge.send_servo(info_to_send.angle)

def main(args=None):
    rclpy.init(args=args)
    node = WheelManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
