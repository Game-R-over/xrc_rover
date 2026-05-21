import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'rover_commands'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')
        ),
        (
            os.path.join('share', package_name, 'urdf'),
            glob('urdf/*')
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='xplore',
    maintainer_email='xplore@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'fsm_node = rover_commands.fsm:main',
            'gamepad = rover_commands.gamepad_publisher:main',
            'wheels_manager = rover_commands.wheels_manager:main',
            'arm_manager = rover_commands.arm_manager:main',
            'odometry_manager = rover_commands.odometry_manager:main',
            'vision = rover_commands.vision:main',
            'ultrasonic_node = rover_commands.ultrasonics_sensors_manager:main',
        ],
    },
)
