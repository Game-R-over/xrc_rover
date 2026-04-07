import rclpy
from rclpy.node import Node

from custom_msg.msg import MoveData, DCSpeed, ServoAngle
from std_msgs.msg import Empty

from .utils.esp import SerialBridge
from .utils.wheels import rover_drive

class WheelsManager(Node):

    subscribers = {
        'move_update': None,
        'emergency_shutdown': None,
    }

    publishers = {
        'dc_speed_update': None,
        'servo_angle_update': None,
    }

    data = {
        'dc_speed_update': DCSpeed(),
        'servo_angle_update': ServoAngle(),
    }

    SERVOS_OFFSET = 5

    def __init__(self):
        super().__init__('wheels_manager')

        self.subscribers['move_update'] = self.create_subscription(
            MoveData,
            'move_update',
            self.move_update_listener_callback,
            10
        )
        self.subscribers['emergency_shutdown'] = self.create_subscription(
            Empty,
            'emergency_shutdown',
            self.emergency_shutdown_listener_callback,
            10
        )

        self.publishers['dc_speed_update'] = self.create_publisher(
            DCSpeed,
            'dc_speed_update',
            10
        )
        self.publishers['servo_angle_update'] = self.create_publisher(
            ServoAngle,
            'servo_angle_update',
            10
        )

        self.get_logger().info('[START]')


    def move_update_listener_callback(self, msg):

        self.get_logger().info(f'Received command: speed={msg.speed}, angle={msg.angle}')

        Vmax = 20
        Kmax = 1
        W = 5
        Lf = 0.5
        Lr = 0.5

        drive_data = rover_drive(msg.x_angle, msg.y_angle, Vmax, Kmax, W, Lf, Lr)

        for dc, speed in drive_data['speeds'].enumerate():
            self.data['dc_speed_update'].speed = speed
            self.data['dc_speed_update'].dc = dc
            self.publish('dc_speed_update')

        for servo, angle in drive_data['angles'].enumerate():
            self.data['servo_angle_update'].angle = speed
            self.data['servo_angle_update'].servo = servo + self.SERVOS_OFFSET
            self.publish('servo_angle_update')

    def emergency_shutdown_listener_callback(self, msg):

        # TODO: Find out what to do (set speed and angles to 0)

        self.get_logger().info('Sending shutdown speed to ESP')

    def publish(topic):
        self.publishers[topic].publish(self.data[topic])

def main(args=None):
    rclpy.init(args=args)
    node = WheelsManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
