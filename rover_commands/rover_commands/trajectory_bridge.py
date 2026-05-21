import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer

from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState


class TrajectoryBridge(Node):

    def __init__(self):
        super().__init__('trajectory_bridge')

        # MoveIt action interface
        self._action_server = ActionServer(
            self,
            FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory',
            execute_callback=self.execute_callback
        )

        # Joint state publisher
        self.joint_pub = self.create_publisher(
            JointState,
            '/joint_states',
            10
        )

        # IMPORTANT:
        # Do NOT hardcode joint order.
        # MoveIt will provide the correct order dynamically.
        self.joint_names = []

        # Simulated actual robot state
        self.current_positions = []

        # Publish robot state continuously
        self.timer = self.create_timer(
            0.02,   # 50 Hz
            self.publish_joint_states
        )

        self.get_logger().info("Trajectory bridge ready")

    # -------------------------------------------------
    # Publish actual robot state to RViz
    # -------------------------------------------------
    def publish_joint_states(self):

        if not self.joint_names:
            return

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()

        # MUST match MoveIt's joint order
        msg.name = self.joint_names
        msg.position = self.current_positions

        self.joint_pub.publish(msg)

    # -------------------------------------------------
    # Execute trajectory from MoveIt
    # -------------------------------------------------
    def execute_callback(self, goal_handle):

        traj = goal_handle.request.trajectory

        self.get_logger().info(
            f"Received trajectory with {len(traj.points)} points"
        )

        # CRITICAL:
        # Use MoveIt's exact joint order
        self.joint_names = list(traj.joint_names)

        # Initialize current positions if first run
        if not self.current_positions:
            self.current_positions = [0.0] * len(self.joint_names)

        result = FollowJointTrajectory.Result()

        previous_positions = list(self.current_positions)
        previous_time = 0.0

        for point in traj.points:

            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info("Trajectory canceled")
                return result

            target_positions = list(point.positions)

            target_time = (
                point.time_from_start.sec +
                point.time_from_start.nanosec * 1e-9
            )

            segment_duration = max(
                target_time - previous_time,
                0.001
            )

            # Smooth interpolation
            rate_hz = 50.0
            dt = 1.0 / rate_hz

            steps = max(int(segment_duration * rate_hz), 1)

            for step in range(steps):

                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    self.get_logger().info("Trajectory canceled")
                    return result

                alpha = (step + 1) / steps

                # Interpolate joint motion
                self.current_positions = [
                    previous_positions[j] +
                    alpha * (target_positions[j] - previous_positions[j])
                    for j in range(len(self.joint_names))
                ]

                # Send to hardware
                self.send_to_robot(self.current_positions)

                # Publish feedback
                feedback = FollowJointTrajectory.Feedback()

                feedback.joint_names = self.joint_names
                feedback.actual.positions = list(self.current_positions)
                feedback.desired.positions = target_positions

                goal_handle.publish_feedback(feedback)

                # Allow ROS callbacks
                rclpy.spin_once(self, timeout_sec=0.0)

                time.sleep(dt)

            previous_positions = target_positions
            previous_time = target_time

        # Final exact target
        self.current_positions = list(
            traj.points[-1].positions
        )

        goal_handle.succeed()

        self.get_logger().info("Trajectory execution complete")

        return result

    # -------------------------------------------------
    # Hardware interface
    # -------------------------------------------------
    def send_to_robot(self, positions):

        # Replace with actual motor commands later
        self.get_logger().debug(
            f"Robot positions: {positions}"
        )


def main():

    rclpy.init()

    node = TrajectoryBridge()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()

