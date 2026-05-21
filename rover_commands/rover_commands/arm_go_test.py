import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import MotionPlanRequest, Constraints, PositionConstraint
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import PoseStamped


class MoveItXYZ(Node):

    def __init__(self):
        super().__init__('moveit_xyz_client')

        self._client = ActionClient(self, MoveGroup, '/move_action')

        self.get_logger().info("Waiting for MoveIt action server...")
        self._client.wait_for_server()
        self.get_logger().info("Connected to MoveIt")

    def go_xyz(self, x, y, z):

        goal = MoveGroup.Goal()

        goal.request.group_name = "arm"

        # --- Build pose constraint ---
        target_pose = PoseStamped()
        target_pose.header.frame_id = "base_link"

        target_pose.pose.position.x = float(x)
        target_pose.pose.position.y = float(y)
        target_pose.pose.position.z = float(z)

        target_pose.pose.orientation.w = 1.0

        constraint = PositionConstraint()
        constraint.header = target_pose.header
        constraint.link_name = "gripper_base_link"

        box = SolidPrimitive()
        box.type = SolidPrimitive.SPHERE
        box.dimensions = [0.01]

        constraint.constraint_region.primitives.append(box)
        constraint.constraint_region.primitive_poses.append(target_pose.pose)

        constraint.weight = 1.0

        c = Constraints()
        c.position_constraints.append(constraint)

        goal.request.goal_constraints.append(c)

        self.get_logger().info(f"Sending XYZ goal: {x}, {y}, {z}")

        future = self._client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected")
            return

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result()

        self.get_logger().info("Motion complete")


def main():
    rclpy.init()
    node = MoveItXYZ()

    # test point (adjust if needed)
    node.go_xyz(0.0, 0.0, 0.2)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

