from launch import LaunchDescription
from launch_ros.actions import Node

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    # Load MoveIt config package
    moveit_config = MoveItConfigsBuilder(
        "rover",
        package_name="moveit_config"
    ).to_moveit_configs()

    # MoveGroup node (core MoveIt runtime)
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),

            # CRITICAL: this fixes your crash
            {
                "moveit_controller_manager":
                    "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            }
        ],
    )

    rviz_file = moveit_config.package_path / "config" / "moveit.rviz"

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", str(rviz_file)],
        parameters=[moveit_config.to_dict()],
    )

    # Static TF (only needed if your URDF doesn’t already provide root frame)
    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "world", "base_footprint"],
    )

    return LaunchDescription([
        static_tf,
        move_group_node,
        rviz_node,
    ])

