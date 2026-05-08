import rclpy
from rclpy.node import Node

from custom_msg.msg import MoveData, DCSpeed, ServoAngle
from std_msgs.msg import Empty, Int32

import time

from .utils.wheels import rover_drive

class WheelsManager(Node):

    history = []

    subscribers = {
        'move_update': None,
        'emergency_shutdown': None,
    }

    publishers = {
        'dc_speed_update': None,
        'servo_angle_update': None,
        'encoder_request': None,
        'speed_change': None,
        'angle_change': None,
    }

    data = {
        'dc_speed_update': DCSpeed(),
        'servo_angle_update': ServoAngle(),
        'encoder_request': Int32(),
        'speed_change': DCSpeed(),
        'angle_change': ServoAngle(),
    }

    SERVOS_OFFSET = 4 + 1
    SERVOS_NUM = 4
    DCS_NUM = 6

    def __init__(self):
        super().__init__('wheels_manager')

        self.subscribers['move_update'] = self.create_subscription(
            MoveData,
            'move_update',
            self.move_update_listener_callback,
            10
        )
        self.subscribers['dc_speed_feedback'] = self.create_subscription(
            DCSpeed,
            'dc_speed_feedback',
            self.dc_speed_feedback_listener_callback,
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
        self.publishers['encoder_request'] = self.create_publisher(
            Int32,
            'encoder_request',
            10
        )
        self.publishers['speed_change'] = self.create_publisher(
            DCSpeed,
            'speed_change',
            10
        )
        self.publishers['angle_change'] = self.create_publisher(
            ServoAngle,
            'angle_change',
            10
        )

        self.timer = self.create_timer(0.1, self.request_encoder_speeds)

        self.get_logger().info('[START]')

    def move_update_listener_callback(self, msg):

        self.get_logger().info(f'Received command: speed={msg.y_speed}, angle={msg.x_angle}')

        Vmax = 20
        Kmax = 1
        W = 5
        Lf = 0.5
        Lr = 0.5

        drive_data = rover_drive(msg.x_angle, msg.y_speed, Vmax, Kmax, W, Lf, Lr)

        for dc, speed in enumerate(drive_data['speeds']):
            self.data['dc_speed_update'].speed = speed
            self.data['dc_speed_update'].dc = dc + 1
            self.publish('dc_speed_update')

        for servo, angle in enumerate(drive_data['angles']):
            self.data['servo_angle_update'].angle = angle
            self.data['servo_angle_update'].servo = servo + self.SERVOS_OFFSET
            self.publish('servo_angle_update')
            self.write_angle(self.data['servo_angle_update'])

    def dc_speed_feedback_listener_callback(self, msg):
        self.data['speed_change'].dc = msg.dc
        self.data['speed_change'].speed = msg.speed
        self.publish('speed_change')

    def emergency_shutdown_listener_callback(self, msg):

        for i in range(self.DCS_NUM):
            self.data['dc_speed_update'].speed = 0
            self.data['dc_speed_update'].dc = i + 1
            self.publish('dc_speed_update')

        for i in range(self.SERVOS_NUM):
            self.data['servo_angle_update'].angle = 0
            self.data['servo_angle_update'].servo = i + self.SERVOS_OFFSET
            self.publish('servo_angle_update')

        self.get_logger().info('Sending shutdown speed to ESP')

    def publish(self, topic):
        self.publishers[topic].publish(self.data[topic])

    def request_encoder_speeds(self):
        for i in range(self.DCS_NUM):
            self.data['encoder_request'].data = i + 1
            self.publish('encoder_request')

    def write_angle(self, msg):
        self.data['angle_change'] = msg
        self.publish('angle_change')

def main(args=None):
    rclpy.init(args=args)
    node = WheelsManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
