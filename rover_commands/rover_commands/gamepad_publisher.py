import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData, GamepadData


class GamepadPublisher(Node):
    user_input_publisher = None
    data = MoveData()
    
    MAX_X_ANGLE = 1
    MAX_Y_SPEED = 1

    SPEED_INCREMENT = 0.1
    ANGLE_INCREMENT = 0.1

    def __init__(self):

        super().__init__('gamepad')

        self.user_input_publisher = self.create_publisher(MoveData, 'user_input', 10) 
        self.get_logger().info('[START]')
        
        self.gamepad_subscriber = self.create_subscription(
            GamepadData,
            'gamepad_input',
            self.get_user_input,
            10
        )
        
    def get_user_input(self, msg):
        
        self.get_logger().info("J'ai reçu un message !")
        self.get_logger().info(f'Reçu: right_x={msg.axis_right_x} right_y={msg.axis_right_y}')
        self.get_logger().info(f'Reçu: left_x={msg.axis_left_x} left_y={msg.axis_left_y} right_x={msg.axis_right_x} right_y={msg.axis_right_y}')
        #is the changement too fast ?
        
        #avoid error static joystic
        if abs(msg.axis_right_y)>0.05:
            self.data.y_speed= msg.axis_right_y
        # value between  -1 and 1
        else: self.data.y_speed=0.0
            
        if abs(msg.axis_right_x)>0.05:
            self.data.x_angle=msg.axis_right_x
        else: self.data.x_angle=0.0
     
        self.user_input_publisher.publish(self.data)
        self.get_logger().info(f'Current data:\n\tspeed:{self.data.y_speed}\n\tangle:{self.data.x_angle}')

def main(args=None):
    rclpy.init(args=args)
    node = GamepadPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
