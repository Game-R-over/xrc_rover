import rclpy
from rclpy.node import Node

from custom_msg.msg import MoveData
from custom_msg.msg import Speed
from std_msgs.msg import Empty

from .utils.esp import SerialBridge

class WheelsManager(Node):

    subscriptions = {
        'move_update': None,
        'emergency_shutdown': None,
    }

    data = MoveData()
    speed_offset = 0.0

    serial_bridge = None

    def __init__(self):
        super().__init__('wheels_manager')

        self.subscriptions['move_update'] = self.create_subscription(
            MoveData,
            'move_update',
            self.move_update_listener_callback,
            10
        )
        self.subscriptions['emergency_shutdown'] = self.create_subscription(
            Empty,
            'emergency_shutdown',
            self.emergency_shutdown_listener_callback,
            10
        )

        self.serial_bridge = SerialBridge(self.get_logger, lambda self, data: print(data))

        self.get_logger().info('Wheels Manager node has been started.')


    def move_update_listener_callback(self, msg):
        self.data.speed = msg.speed
        self.data.angle = msg.angle
        self.send_to_esp(self.data)

        self.get_logger().info(f'Received command: speed={msg.speed}, angle={msg.angle}')

    def emergency_shutdown_listener_callback(self, msg):
        self.data.speed = 0.0

        self.send_to_esp(self.data)

        self.get_logger().info('Sending shutdown speed to ESP')

    def send_to_esp(self, info_to_send):
        self.serial_bridge.send_motor(info_to_send.speed)
        self.serial_bridge.send_servo(info_to_send.angle)

        self.get_logger().info(f'Getting data {datas[1:]} from ESP')

def main(args=None):
    rclpy.init(args=args)
    node = WheelManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
