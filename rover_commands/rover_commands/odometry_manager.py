import rclpy
from rclpy.node import Node

from custom_msg.msg import DCSpeed, ServoAngle
from std_msgs.msg import Empty
from nav_msgs.msg import Odometry

import math

class OdometryManager(Node):

    subscribers = {
        'speed_change': None,
        'angle_change': None,
        'emergency_shutdown': None,
    }

    publishers = {
        'odometry_update': None,
    }

    data = {
        'odometry_update': Odometry(),
    }

    SERVOS_OFFSET = 4 + 1

    state = [0.0, 0.0, 0.0] # [x, y, theta]
    wheel_speeds = [0.0] * 6
    steering_angles = [0.0] * 4

    dt = 0.02

    Lf = 10 # distance from center to front axle
    Lr = 10 # distance from center to rear axle

    def __init__(self):
        super().__init__('odometry_manager')

        self.subscribers['speed_change'] = self.create_subscription(
            DCSpeed,
            'speed_change',
            self.speed_change_listener_callback,
            10
        )
        self.subscribers['angle_change'] = self.create_subscription(
            ServoAngle,
            'angle_change',
            self.angle_change_listener_callback,
            10
        )
        self.subscribers['emergency_shutdown'] = self.create_subscription(
            Empty,
            'emergency_shutdown',
            self.emergency_shutdown_listener_callback,
            10
        )

        self.publishers['odometry_update'] = self.create_publisher(
            Odometry,
            'odometry_update',
            10
        )

        self.timer = self.create_timer(self.dt, self.update_odometry)

        self.get_logger().info('[START]')

    def speed_change_listener_callback(self, msg):
        self.wheel_speeds[msg.dc - 1] = msg.speed

    def angle_change_listener_callback(self, msg):
        self.steering_angles[msg.servo - self.SERVOS_OFFSET] = msg.angle

    def emergency_shutdown_listener_callback(self, msg):
        ...

    def update_odometry(self):

        # TODO: Check if FL, FR, BL, BR are right

        v = sum(self.wheel_speeds) / 6.0

        delta_f = (
            self.steering_angles[0] + # FL
            self.steering_angles[1] # FR
        ) / 2.0

        delta_r = (
            self.steering_angles[2] + # BL
            self.steering_angles[3] # BR
        ) / 2.0

        omega = (
            v / (self.Lf + self.Lr)
        ) * (
            math.tan(delta_f) -
            math.tan(delta_r)
        )

        self.state[0] += v * math.cos(self.state[2]) * self.dt
        self.state[1] += v * math.sin(self.state[2]) * self.dt
        self.state[2] += omega * self.dt

def main(args=None):
    rclpy.init(args=args)
    node = OdometryManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
