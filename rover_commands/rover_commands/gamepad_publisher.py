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
            'gamepad_input',
            self.get_user_input,
            10
        )

        self.gamepad_race_subscriber = self.create_subscription(
            Int32,
            'gamepad_race_input',
            self.get_race_input,
            10
        )


        self.arm_position.x = 30.
        self.arm_position.y = -20.

    def validate_cordinates(self):

        if self.arm_position.x < 0:
            self.arm_position.x = max(self.arm_position.x, self.X_ARM_MIN)
        if self.arm_position.y < 0:
            self.arm_position.y = max(self.arm_position.y, self.Y_ARM_MIN)

        origine_distance = math.sqrt(self.arm_position.x**2+self.arm_position.y**2)

        if origine_distance > self.RADIUS:
          self.arm_position.x =  self.arm_position.x / origine_distance * self.RADIUS
          self.arm_position.y = self.arm_position.y / origine_distance * self.RADIUS


    def get_race_input(self, msg):
        if msg.data == 0:
            self.RACE_MODE =0
        else :
            self.RACE_MODE = 1
        self.get_logger().info(f'race mode received\n\tmode:{self.RACE_MODE}')
    

    def get_user_input(self, msg):

        # DCs + Servos

        if self.RACE_MODE == 0:
            self.data.y_speed = msg.axis_right_y if abs(msg.axis_right_y) > 0.05 else 0.0
            self.data.x_angle = msg.axis_right_x if abs(msg.axis_right_x) > 0.05 else 0.0
     
        else: 
            self.data.y_speed = msg.axis_right_y if abs(msg.axis_right_y) > 0.05 else 0.0
            if abs(msg.axis_right_x) > 0.7:
                self.data.x_angle = msg.axis_right_x -msg.axis_right_x/abs(msg.axis_right_x) * 0.7  
            else: 
                self.data.x_angle = 0.0

        self.user_input_wheels_publisher.publish(self.data)
        self.get_logger().info(f'Current data:\n\tspeed:{self.data.y_speed}\n\tangle:{self.data.x_angle}')
        


        # ARM Angle
    
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
