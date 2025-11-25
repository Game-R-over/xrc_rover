import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData

class WheelManager(Node):

    def __init__(self):
        super().__init__('wheel_manager')

        self.subscription = self.create_subscription(
            MoveData,
            'wheel_update',
            self.listener_callback,
            10
        )

        self.get_logger().info('Wheel Manager node has been started.')
        self.deltadata= {}


    def listener_callback(self, msg):
        self.get_logger().info('Response')
        self.deltadata['speed'] = msg.speed
        self.deltadata['angle'] = msg.angle

        self.send_to_esp(msg)

        self.get_logger().info(f'Received command: deltaspeed={msg.speed}, deltaangle={msg.angle}')

    def send_to_esp(self, info_to_send):
        #info à envoyer à flow
        ...

def main(args=None):
    rclpy.init(args=args)
    node = WheelManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
