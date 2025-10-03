import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class TrajectorySubscriber(Node):

    def __init__(self):
        super().__init__('trajectory_subscriber')
        
        self.subscription = self.create_subscription(
            Twist,
            'velocity',
            self.listener_callback,
            10
        )
        self.subscription

        self.get_logger().info('Subscriber node has been started.')
        self.position = {'x': 0.0, 'z': 0.0, 'ry': 0.0}

    def listener_callback(self, msg):
        self.position['x'] += msg.linear.x
        self.position['z'] += msg.linear.z
        self.position['ry'] += msg.angular.y

        self.get_logger().info(f'New Position: {self.position}')

def main(args=None):
    rclpy.init(args=args)
    node = TrajectorySubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()