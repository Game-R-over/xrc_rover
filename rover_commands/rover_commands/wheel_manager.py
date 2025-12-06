import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData
from .utils.esp import SerialBridge
from std_msgs.msg import Empty

class WheelManager(Node):

    subscription = None
    data = None
    serial_bridge = None

    def __init__(self):
        super().__init__('wheel_manager')

        self.subscription = self.create_subscription(
            MoveData,
            'wheel_update',
            self.listener_callback,
            10
        )

        self.subscription = self.create_subscription(
            Empty,
            'emergency_shutdown',
            self.listener_callback_shutdown,
            10
        )

        self.serial_bridge = SerialBridge(self.get_logger)
        self.data = MoveData()

        self.get_logger().info('Wheel Manager node has been started.')


    def listener_callback(self, msg):
        self.get_logger().info('Response')
        self.data = msg
        self.send_to_esp(msg)

        self.get_logger().info(f'Received command: speed={msg.speed}, angle={msg.angle}')
   
    def listener_callback_shutdown(self,msg):
        self.data.speed = 0
        
        self.send_to_esp(self.data)
        
        self.get_logger().info('Sending shutdown speed to ESP')
   
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
