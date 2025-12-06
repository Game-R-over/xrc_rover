import rclpy
from rclpy.node import Node

from custom_msg.msg import MoveData
from custom_msg.msg import Speed
from std_msgs.msg import Empty

from .utils.esp import SerialBridge

class WheelManager(Node):

    wheel_update_subscription = None
    emergency_shutdown_subscription = None
    effective_wheel_publisher = None

    data = MoveData()
    speed_offset = 0.0

    serial_bridge = None

    def __init__(self):
        super().__init__('wheel_manager')

        self.wheel_update_subscription = self.create_subscription(
            MoveData,
            'wheel_update',
            self.wheel_update_listener_callback,
            10
        )

        self.wheel_diff_subscription = self.create_subscription(
            Speed,
            'wheel_diff',
            self.wheel_diff_listener_callback,
            10
        )

        self.emergency_shutdown_subscription = self.create_subscription(
            Empty,
            'emergency_shutdown',
            self.emergency_shutdown_listener_callback,
            10
        )

        self.effective_wheel_publisher = self.create_publisher(
            Speed,
            'effective_wheel',
            10
        )

        self.serial_bridge = SerialBridge(self.get_logger, self.send_to_effective)

        self.get_logger().info('Wheel Manager node has been started.')


    def wheel_update_listener_callback(self, msg):
        self.data.speed = msg.speed + self.speed_offset
        self.data.angle = msg.angle
        self.send_to_esp(self.data)

        # For TESTING ONLY
        # self.send_to_effective(f'OK RPM {msg.speed + 5}')

        self.get_logger().info(f'Received command: speed={msg.speed}, angle={msg.angle}, with speed diff {self.speed_offset}')

    def wheel_diff_listener_callback(self, msg):
        self.speed_offset = msg.speed

        self.get_logger().info(f'Fixing diff : speed={msg.speed}')

    def emergency_shutdown_listener_callback(self, msg):
        self.data.speed = 0.0

        self.send_to_esp(self.data)

        self.get_logger().info('Sending shutdown speed to ESP')

    def send_to_esp(self, info_to_send):
        self.serial_bridge.send_motor(info_to_send.speed)
        self.serial_bridge.send_servo(info_to_send.angle)

    def send_to_effective(self, data):
        datas = data.split()
        if datas[0] == 'ERR':
            self.get_logger().error(' '.join(datas[1:]))
            return

        if datas[1] == 'RPM':
            speed = Speed()
            speed.speed = float(datas[2])
            self.effective_wheel_publisher.publish(speed)

        self.get_logger().info(f'Getting data {datas[1:]} from ESP')

def main(args=None):
    rclpy.init(args=args)
    node = WheelManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
