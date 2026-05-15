import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData, GamepadData, Vec2
from std_msgs.msg import Int32

import math

class GamepadPublisher(Node):
    user_input_wheels_publisher = None
    user_input_arm_position_publisher = None
    user_input_arm_angle_publisher = None

    MIN_ARM_BASE_ANGLE = 0
    MAX_ARM_BASE_ANGLE = 180
    DEFAULT_ARM_BASE_ANGLE = 90
    ANGLE_INCREMENT = 5

    ARM_RANGE = 800
    MIN_ARM_CLAW_ANGLE = 0
    MAX_ARM_CLAW_ANGLE = 90
    DEFAULT_ARM_CLAW_ANGLE = 90

    data = MoveData()
    arm_base_angle = DEFAULT_ARM_BASE_ANGLE
    arm_claw_angle = DEFAULT_ARM_CLAW_ANGLE
    arm_position = Vec2()


    def __init__(self):

        super().__init__('gamepad')

        self.user_input_wheels_publisher = self.create_publisher(MoveData, 'user_input', 10)
        self.user_input_arm_position_publisher = self.create_publisher(Vec2, 'arm_position_update', 10) 
        self.user_input_arm_angle_publisher = self.create_publisher(Int32, 'arm_angle_update', 10) 
        self.user_input_arm_claw_publisher= self.create_publisher(Int32,'arm_claw_update', 10)

        self.get_logger().info('[START]')
        
        self.gamepad_subscriber = self.create_subscription(
            GamepadData,
            'gamepad_input',
            self.get_user_input,
            10
        )
        
    def get_user_input(self, msg):

        # DCs + Servos
        
        if abs(msg.axis_right_y) > 0.05:
            self.data.y_speed = msg.axis_right_y
        else: self.data.y_speed = 0.0
            
        if abs(msg.axis_right_x) > 0.05:
            self.data.x_angle = msg.axis_right_x
        else: self.data.x_angle = 0.0
     
        self.user_input_wheels_publisher.publish(self.data)
        self.get_logger().info(f'Current data:\n\tspeed:{self.data.y_speed}\n\tangle:{self.data.x_angle}')
        
        # ARM Angle
    
        if msg.trigger_left > 0.5:
            self.arm_base_angle = max(self.arm_base_angle - self.ANGLE_INCREMENT, self.MIN_ARM_BASE_ANGLE)
        
        if msg.trigger_right > 0.5 and self.arm_base_angle < self.MAX_ARM_BASE_ANGLE - self.ANGLE_INCREMENT:
            self.arm_base_angle = min(self.arm_base_angle + self.ANGLE_INCREMENT, self.MAX_ARM_BASE_ANGLE)
        
        angle_message = Int32()
        angle_message.data = self.arm_base_angle

        self.user_input_arm_angle_publisher.publish(angle_message)

        # CLAW Angle
        
        if msg.button_left == 1 and self.angle_claw_arm > self.MIN_ARM_CLAW_ANGLE:
            self.angle_claw_arm -= self.ANGLE_INCREMENT
        
        if msg.button_right == 1 and self.angle_claw_arm < self.MAX_ARM_CLAW_ANGLE:
            self.angle_claw_arm += self.ANGLE_INCREMENT
        
        claw_message = Int32()
        claw_message.data = self.angle_claw_arm
        self.user_input_arm_claw_publisher.publish(claw_message)

        self.arm_position.x = math.floor(msg.axis_left_x * self.ARM_RANGE)
        self.arm_position.y = math.floor(msg.axis_left_y * self.ARM_RANGE)

        self.user_input_arm_position_publisher.publish(self.arm_position)

def main(args=None):
    rclpy.init(args=args)
    node = GamepadPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
