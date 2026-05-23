import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('rover_commands')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    params_file = os.path.join(pkg_dir, 'config', 'nav2_params.yaml')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=params_file,
            description='Full path to the ROS2 parameters file to use for all launched nodes'
        ),
        
        # Static TF: base_footprint -> camera_link
        # Assuming the camera is mounted 0.2m high, facing forward
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0.2', '0', '0', '0', 'base_footprint', 'camera_link']
        ),
        
        # Core Rover Nodes
        Node(
            package='rover_commands',
            executable='wheels_manager',
            name='wheels_manager'
        ),
        Node(
            package='rover_commands',
            executable='ekf',
            name='ekf_node'
        ),
        Node(
            package='rover_commands',
            executable='vision',
            name='vision_node'
        ),
        Node(
            package='rover_commands',
            executable='aruco_detector',
            name='aruco_detector'
        ),
        
        # Include the official Nav2 navigation launch file (skipping AMCL and map_server)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
            ),
            launch_arguments={
                'use_sim_time': 'False',
                'params_file': LaunchConfiguration('params_file'),
                'autostart': 'True',
                'use_composition': 'False'
            }.items(),
        )
    ])