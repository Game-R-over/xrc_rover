import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from geometry_msgs.msg import PoseStamped, TransformStamped

from scipy.spatial.transform import Rotation as R
from tf2_ros import TransformBroadcaster

import numpy as np
import math

from .ekf.EKF import EKF

def quat_from_euler(roll, pitch, yaw):
    return R.from_euler('xyz', [roll, pitch, yaw]).as_quat()

def quat_to_yaw(self, q):
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)

    return math.atan2(siny_cosp, cosy_cosp)


class EKFNode(Node):

    def __init__(self):
        super().__init__("ekf_node")

        self.tf_broadcaster = TransformBroadcaster(self)

        x0 = np.array([
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ])  # [x, y, theta, vx, vy, omega, b]

        P0 = np.diag([1e-2, 1e-2, 1e-2, 1e-2, 1e-2, 1e-2, 1e-3])
        Q = np.diag([1e-4, 1e-4, 1e-4, 1e-3, 1e-3, 1e-4, 1e-6])
        R_aruco = np.diag([0.05, 0.05, 0.05])
        R_imu = np.diag([0.05, 0.05])

        self.ekf = EKF(x0, P0, Q, R_aruco, R_imu)

        self.dt = 0.02
        self.last_time = self.get_clock().now()

        self.state_inputs = np.array([0.0, 0.0]) # (vxm, vym)
        self.subscribers = {
            '/odom/wheel': self.create_subscription(
                Odometry,
                '/odom/wheel',
                self.wheel_callback,
                10
            ),
            '/imu/data/': self.create_subscription(
                Imu,
                '/imu/data',
                self.imu_callback,
                10
            ),
            '/vision/pose': self.create_subscription(
                PoseStamped,
                '/vision/pose',
                self.vision_callback,
                10
            ),
        }

        self.odom_pub = self.create_publisher(
            Odometry,
            '/odometry/filtered',
            10
        )

        self.timer = self.create_timer(self.dt, self.update)

        self.get_logger().info("EKF Node started")

    def wheel_callback(self, msg: Odometry):
        self.state_inputs[0] = msg.twist.twist.linear.x
        self.state_inputs[1] = msg.twist.twist.linear.y

    def imu_callback(self, msg: Imu):
        theta = quat_to_yaw(msg.orientation)
        omega = msg.angular_velocity.z

        self.ekf.update_imu(np.array([theta, omega]))

    def vision_callback(self, msg: PoseStamped):

        x = msg.pose.position.x
        y = msg.pose.position.y

        theta = quat_to_yaw(msg.pose.orientation)

        self.ekf.update_aruco(np.array([x, y, theta]))

    def update(self):

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now

        self.ekf.predict(self.state_inputs, dt)

        self.publish_odometry(now)
        self.publish_tf(now)

    def publish_odometry(self, now):

        x, y, theta, vx, vy, omega, b = self.ekf.x

        q = quat_from_euler(0, 0, theta)

        msg = Odometry()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = "map"
        msg.child_frame_id = "base_footprint"

        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.orientation.x = q[0]
        msg.pose.pose.orientation.y = q[1]
        msg.pose.pose.orientation.z = q[2]
        msg.pose.pose.orientation.w = q[3]

        msg.twist.twist.linear.x = vx
        msg.twist.twist.linear.y = vy
        msg.twist.twist.angular.z = omega - b

        self.odom_pub.publish(msg)

    def publish_tf(self, now):

        x, y, theta, _, _, _, _ = self.ekf.x
        q = quat_from_euler(0, 0, theta)

        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = "map"
        t.child_frame_id = "base_footprint"

        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.translation.z = 0.0

        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]

        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = EKFNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
