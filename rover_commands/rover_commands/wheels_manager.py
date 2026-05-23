import rclpy
from rclpy.node import Node

from custom_msg.msg import MoveData, DCSpeed, ServoAngle
from std_msgs.msg import Empty, Int32
from geometry_msgs.msg import Twist

import time
import math

from .utils.wheels import rover_drive

class WheelsManager(Node):

    SERVOS_OFFSET = 4 + 1
    SERVOS_NUM = 4
    DCS_NUM = 6

    def __init__(self):
        super().__init__('wheels_manager')

        self.subscribers = {}
        self.publishers_dict = {}

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
        
        # NAV2 Twist subscriber
        self.subscribers['cmd_vel'] = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.publishers_dict['dc_speed_update'] = self.create_publisher(DCSpeed, 'dc_speed_update', 10)
        self.publishers_dict['servo_angle_update'] = self.create_publisher(ServoAngle, 'servo_angle_update', 10)
        self.publishers_dict['encoder_request'] = self.create_publisher(Int32, 'encoder_request', 10)
        self.publishers_dict['speed_change'] = self.create_publisher(DCSpeed, 'speed_change', 10)
        self.publishers_dict['angle_change'] = self.create_publisher(ServoAngle, 'angle_change', 10)

        self.data = {
            'dc_speed_update': DCSpeed(),
            'servo_angle_update': ServoAngle(),
            'encoder_request': Int32(),
            'speed_change': DCSpeed(),
            'angle_change': ServoAngle(),
        }

        self.timer = self.create_timer(0.1, self.request_encoder_speeds)
        self.get_logger().info('[START]')

    def move_update_listener_callback(self, msg):
        Vmax = 255
        Kmax = 5
        W = 0.5
        Lf = 0.3
        Lr = 0.25

        drive_data = rover_drive(msg.x_angle, msg.y_speed, Vmax, Kmax, W, Lf, Lr)

        for dc, speed in enumerate(drive_data['speeds']):
            if msg.y_speed != 0:
                self.data['dc_speed_update'].speed = speed/Vmax*100 + speed / abs(speed)*155
            else:
                self.data['dc_speed_update'].speed = 0.0

            self.data['dc_speed_update'].dc = dc + 1
            self.publish('dc_speed_update')
            time.sleep(0.005)

        for servo, angle in enumerate(drive_data['angles']):
            self.data['servo_angle_update'].angle = angle*180/math.pi+90
            self.data['servo_angle_update'].servo = servo + self.SERVOS_OFFSET
            self.publish('servo_angle_update')
            self.write_angle(self.data['servo_angle_update'])

    def cmd_vel_callback(self, msg):
        # Convert Nav2 Twist (m/s and rad/s) to the rover's expected normalized inputs [-1, 1]
        move_msg = MoveData()
        move_msg.y_speed = max(min(msg.linear.x, 1.0), -1.0)
        move_msg.x_angle = max(min(msg.angular.z, 1.0), -1.0)
        
        # Route it through the exact same custom geometry math as the gamepad
        self.move_update_listener_callback(move_msg)

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
        self.publishers_dict[topic].publish(self.data[topic])

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
