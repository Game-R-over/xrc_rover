import rclpy
from rclpy.node import Node

from custom_msg.msg import MoveData
from custom_msg.msg import Speed
from std_msgs.msg import Empty

from threading import Timer

from .utils.esp import SerialBridge

class EffectiveCheck(Node):

    wheel_update_subscription = None
    effective_wheel_subscription = None
    wheel_diff_publisher = None

    data = MoveData()
    effective_speed = 0
    timer = None

    def __init__(self):
        super().__init__('effective_check')

        self.wheel_update_subscription = self.create_subscription(
            MoveData,
            'wheel_update',
            self.wheel_update_listener_callback,
            10
        )

        self.effective_wheel_subscription = self.create_subscription(
            Speed,
            'effective_wheel',
            self.effective_wheel_listener_callback,
            10
        )

        self.wheel_diff_publisher = self.create_publisher(
            Speed,
            'wheel_diff',
            10
        )


        self.get_logger().info('Effective check node has been started.')

    def wheel_update_listener_callback(self, msg):
        if self.timer != None:
            return

        self.data = msg
        self.timer = Timer(3, self.timeout_check)
        self.timer.start()

        self.get_logger().info(f'Received command: speed={msg.speed}, angle={msg.angle}')
   
    def effective_wheel_listener_callback(self, msg):

        if self.timer == None:
            return

        self.effective_speed = msg.speed

        self.try_compare_speed()

    def try_compare_speed(self):
        speed_diff = Speed()
        speed_diff.speed = self.data.speed - self.effective_speed

        self.timer.cancel()
        self.timer = None

        '''if speed_diff.speed != 0:
            self.wheel_diff_publisher.publish(speed_diff)
            self.get_logger().info(f'Effective displacement {speed_diff.speed}')'''

    def timeout_check(self):
        self.timer = None
        self.get_logger().error('Timeout on effective check')



def main(args=None):
    rclpy.init(args=args)
    node = EffectiveCheck()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
