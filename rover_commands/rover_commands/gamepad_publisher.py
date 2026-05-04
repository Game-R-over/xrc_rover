import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData, GamepadData, Vec2
from std_msgs.msg import Int32


class GamepadPublisher(Node):

    user_input_wheels_publisher = None
    user_input_arm_position_publisher = None
    user_input_arm_angle_publisher = None

    MIN_ARM_BASE_ANGLE = 0
    MAX_ARM_BASE_ANGLE = 180
    DEFAULT_ARM_BASE_ANGLE = 90
    ANGLE_INCREMENT = 5

    ARM_RANGE = 80

    data = MoveData()
    arm_base_angle = DEFAULT_ARM_BASE_ANGLE
    arm_position = Vec2()


    def __init__(self):

        super().__init__('gamepad')

        self.user_input_wheels_publisher = self.create_publisher(MoveData, 'user_input', 10)
        self.user_input_arm_position_publisher = self.create_publisher(Vec2, 'arm_position_update', 10) 
        self.user_input_arm_angle_publisher = self.create_publisher(Int32, 'arm_angle_update', 10) 

        self.get_logger().info('[START]')
        
        self.gamepad_subscriber = self.create_subscription(
            GamepadData,
            'gamepad_input',
            self.get_user_input,
            10
        )
        
    def get_user_input(self, msg):
        
        # Y: SPEED and X: ANGLE
        
        self.data.y_speed = msg.axis_right_y if abs(msg.axis_right_y) > 0.05 else 0.0
        self.data.x_angle = msg.axis_right_x if abs(msg.axis_right_x) > 0.05 else 0.0
     
        self.user_input_wheels_publisher.publish(self.data)
        self.get_logger().info(f'Current data:\n\tspeed:{self.data.y_speed}\n\tangle:{self.data.x_angle}')
        
        # ARM Angle
    
        if msg.trigger_left > 0.5:
            self.angle_base_arm = max(self.angle_base_arm - self.ANGLE_INCREMENT, self.MIN_ARM_BASE_ANGLE)
        
        if msg.trigger_right > 0.5 and self.angle_base_arm < self.MAX_ARM_BASE_ANGLE - self.ANGLE_INCREMENT:
            self.angle_base_arm = min(self.angle_base_arm + self.ANGLE_INCREMENT, self.MAX_ARM_BASE_ANGLE)
        
        angle_message = Int32()
        angle_message.data = self.angle_base_arm
        self.user_input_arm_angle_publisher.publish(angle_message)

        # ARM Position

        self.position_arm.x = msg.axis_left_x * self.RANGE_ARM
        self.position_arm.y = msg.axis_left_y * self.RANGE_ARM

        self.user_input_arm_position_publisher.publish(self.position_arm)

def main(args=None):
    rclpy.init(args=args)
    node = GamepadPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
