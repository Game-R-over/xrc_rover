from launch import LaunchDescription
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

import os
import xacro


def generate_launch_description():

    pkg_path = get_package_share_directory(
        'rover_commands'
    )

    xacro_path = os.path.join(
        pkg_path,
        'urdf',
        'rover.urdf.xacro'
    )

    robot_description_config = xacro.process_file(
        xacro_path
    )

    robot_description = {
        'robot_description':
            robot_description_config.toxml()
    }

    return LaunchDescription([

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',

            parameters=[robot_description],

            output='screen'
        )

    ])
