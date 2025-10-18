import rclpy
from rclpy.node import Node
from custom_msg.msg import OperateTurnstile

class TurnstileOperator(Node):

    def __init__(self):
        super().__init__('turnstile_operator')

        self.publisher_ = self.create_publisher(
            OperateTurnstile,
            'turnstile_topic',
            10
        )

        self.get_logger().info('Publisher node has been started.')

        while rclpy.ok():
            action = input('\n1. Push\n2. Coin\n> ')
            if action == 'q':
                break
            if action != '1' and action != '2':
                self.get_logger().error(f'Invalid input "{action}"')
                break

            # Push - true
            # Coin - false

            msg = OperateTurnstile()
            msg.action = action == '1'
            self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)   # Init ROS python
    node = TurnstileOperator()  # Create a Node instance
    rclpy.spin(node)  # Run the node in a Thread
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
