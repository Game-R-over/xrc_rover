import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from custom_msg.srv import CheckPosition

class TrajectorySubscriber(Node):

    def __init__(self):
        super().__init__('trajectory_subscriber')

        self.subscription = self.create_subscription(
            Twist,
            'position',
            self.listener_callback,
            10
        )

        self.client = self.create_client(CheckPosition, 'check_position')
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.request = CheckPosition.Request()

        self.get_logger().info('Subscriber node has been started.')
        self.position = {'x': 0.0, 'z': 0.0, 'ry': 0.0}

    def send_request(self, x, z):
        self.request.x = x
        self.request.z = z
        self.future = self.client.call_async(self.request)
        '''while not self.future.done():
            self.future = self.cli.call_async(self.req)
            self.get_logger().info(f'{self.future.done()}')
            '''

        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

    def listener_callback(self, msg):
        self.get_logger().info('Response')
        self.position['x'] += msg.linear.x
        self.position['z'] += msg.linear.z
        self.position['ry'] += msg.angular.y

        self.get_logger().info('Response')
        response = self.send_request(self.position['x'], self.position['z'])
        is_allowed = response.is_allowed
        suggestion = response.suggestion
        self.get_logger().info('Response')

        self.get_logger().info(f'Response: is_allowed={is_allowed}, suggestion="{suggestion}"')
        self.get_logger().info(f'New Position: {self.position}')

def main(args=None):
    rclpy.init(args=args)
    node = TrajectorySubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
