import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData, GamepadData, Vec2
from std_msgs.msg import Int32, Empty

import math

class GamepadPublisher(Node):
    user_input_wheels_publisher = None
    user_input_arm_position_publisher = None
    user_input_arm_angle_publisher = None

    MIN_ARM_BASE_ANGLE = 0
    MAX_ARM_BASE_ANGLE = 180
    DEFAULT_ARM_BASE_ANGLE = 90
    ANGLE_INCREMENT = 0.2

    ARM_RANGE = 800
    MIN_ARM_CLAW_ANGLE = 0
    MAX_ARM_CLAW_ANGLE = 90
    DEFAULT_ARM_CLAW_ANGLE = 90
    ANGLE_INCREMENT_CLAW= 1

    data = MoveData()
    arm_base_angle = DEFAULT_ARM_BASE_ANGLE
    arm_claw_angle = DEFAULT_ARM_CLAW_ANGLE
    arm_position = Vec2()

    SPEED_ARM=0.2
    RADIUS = 53
    X_ARM_MIN = 0.
    Y_ARM_MIN = -25.


    RACE_MODE = 0

    def __init__(self):

        super().__init__('gamepad')

        self.user_input_wheels_publisher = self.create_publisher(MoveData, 'user_input', 10)
        self.user_input_arm_position_publisher = self.create_publisher(Vec2, 'arm_position_update', 10) 
        self.user_input_arm_angle_publisher = self.create_publisher(Int32, 'arm_angle_update', 10) 
        self.user_input_arm_claw_publisher= self.create_publisher(Int32, 'arm_claw_update', 10)

        self.get_logger().info('[START]')
        
        self.gamepad_subscriber = self.create_subscription(
            GamepadData,
          
    
        if msg.trigger_left > 0.5:
            self.arm_base_angle = max(self.arm_base_angle + self.ANGLE_INCREMENT, self.MIN_ARM_BASE_ANGLE)
        
        if msg.trigger_right > 0.5:
            self.arm_base_angle = min(self.arm_base_angle - self.ANGLE_INCREMENT, self.MAX_ARM_BASE_ANGLE)
        
        self.get_logger().info(f'Current data:\n\tangle:{self.arm_base_angle}')
        
        angle_message = Int32()
        angle_message.data = math.floor(self.arm_base_angle)

        self.user_input_arm_angle_publisher.publish(angle_message)

        # CLAW Angle
        
        if msg.button_left == 1 and self.arm_claw_angle > self.MIN_ARM_CLAW_ANGLE:
            self.arm_claw_angle -= self.ANGLE_INCREMENT_CLAW
        
        if msg.button_right == 1 and self.arm_claw_angle < self.MAX_ARM_CLAW_ANGLE:
            self.arm_claw_angle += self.ANGLE_INCREMENT_CLAW
        
        claw_message = Int32()
        claw_message.data = self.arm_claw_angle
        self.user_input_arm_claw_publisher.publish(claw_message)

        # ARM Position
         
        self.arm_position.x -= msg.axis_left_x * self.SPEED_ARM if abs(msg.axis_left_x) > 0.05 else 0.0
        self.arm_position.y += msg.axis_left_y * self.SPEED_ARM  if abs(msg.axis_left_y) > 0.05 else 0.0
    
        
        self.validate_cordinates()
   
        
        self.get_logger().info(f'Current data:\n\tposXarm:{self.arm_position.x}\n\tposYarm:{self.arm_position.y}')
    
        self.user_input_arm_position_publisher.publish(self.arm_position)

def main(args=None):
    rclpy.init(args=args)
    node = GamepadPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
