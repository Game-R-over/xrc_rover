import rclpy
from rclpy.node import Node

from custom_msg.msg import DCSpeed, ServoAngle
from std_msgs.msg import Empty
from nav_msgs.msg import Odometry

import numpy as np
import math


class WheelOdometry(Node):

    SERVOS_OFFSET = 5

    def __init__(self):
        super().__init__('wheel_odometry')

        self.dt = 0.02

        self.Lf = 0.30
        self.Lr = 0.25
        self.TRACK = 0.50

        self.wheel_positions = {
            'FL': (+self.Lf, +self.TRACK / 2),
            'FR': (+self.Lf, -self.TRACK / 2),

            'ML': (0.0, +self.TRACK / 2),
            'MR': (0.0, -self.TRACK / 2),

            'BL': (-self.Lr, +self.TRACK / 2),
            'BR': (-self.Lr, -self.TRACK / 2),
        }

        self.wheel_speeds = [0.0] * 6
        self.angles = [0.0] * 4

        self.create_subscription(
            DCSpeed,
            'speed_change',
            self.speed_callback,
            10
        )
        self.create_subscription(
            ServoAngle,
            'angle_change',
            self.angle_callback,
            10
        )
        self.create_subscription(
            Empty,
            'emergency_shutdown',
            self.shutdown_callback,
            10
        )

        self.odom_publisher = self.create_publisher(
            Odometry,
            '/odom/wheel',
            10
        )

        self.timer = self.create_timer(
            self.dt,
            self.update
        )

        self.get_logger().info('Wheel odometry started')


    def speed_callback(self, msg):
        self.wheel_speeds[msg.dc - 1] = msg.speed

    def angle_callback(self, msg):
        self.angles[msg.servo - self.SERVOS_OFFSET] = msg.angle

    def shutdown_callback(self, msg):
        pass

    def compute_speeds(self):

        alphas = {
            servo: self.angles[i]
            for i, servo in enumerate(('FL', 'FR', 'BL', 'BR'))
        }

        vs = {
            motor: self.wheel_speeds[i]
            for i, motor in enumerate(('FL', 'FR', 'ML', 'MR', 'BL', 'BR'))
        }

        A_rows = []
        b_rows = []

        for name in vs.keys():

            alpha = alphas.get(name, 0.0)
            v = vs[name]

            x, y = self.wheel_positions[name]

            sina = math.sin(alpha)
            cosa = math.cos(alpha)

            # No-slip constraint
            A_rows.append([
                -sina,
                cosa,
                sina * y + cosa * x
            ])
            b_rows.append(0.0)

            # Rolling constraint
            A_rows.append([
                cosa,
                sina,
                -cosa * y - sina * x
            ])
            b_rows.append(v)

        A = np.array(A_rows)
        b = np.array(b_rows)

        xi, *_ = np.linalg.lstsq(A, b, rcond=None)

        vx, vy, omega = xi

        return vx, vy, omega

    def publish_odometry(self, vx, vy, omega):

        msg = Odometry()

        current_time = self.get_clock().now()

        msg.header.stamp = current_time.to_msg()

        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'base_footprint'

        # Unknown pose (very high covariance)
        msg.pose.pose.orientation.w = 1.0
        msg.pose.covariance = [
            1e6, 0.0,   0.0,   0.0,   0.0,    0.0,
            0.0,   1e6, 0.0,   0.0,   0.0,    0.0,
            0.0,   0.0,   1e6, 0.0,   0.0,    0.0,
            0.0,   0.0,   0.0,   1e6, 0.0,    0.0,
            0.0,   0.0,   0.0,   0.0,   1e6,  0.0,
            0.0,   0.0,   0.0,   0.0,   0.0,    1e6
        ]

        msg.twist.twist.linear.x = float(vx)
        msg.twist.twist.linear.y = float(vy)
        msg.twist.twist.angular.z = float(omega)
        msg.twist.covariance = [
            0.05, 0.0,  0.0,  0.0,  0.0,    0.0,
            0.0,  0.05, 0.0,  0.0,  0.0,    0.0,
            0.0,  0.0,  1e6, 0.0,  0.0,    0.0,
            0.0,  0.0,  0.0,  1e6, 0.0,    0.0,
            0.0,  0.0,  0.0,  0.0,  1e6,   0.0,
            0.0,  0.0,  0.0,  0.0,  0.0,    0.1
        ]

        self.odom_publisher.publish(msg)

    def update(self):
        self.publish_odometry(*self.compute_speeds())


def main(args=None):
    rclpy.init(args=args)
    node = WheelOdometry()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
