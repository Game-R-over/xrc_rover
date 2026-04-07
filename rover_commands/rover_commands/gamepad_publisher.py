import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData


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

        while True:
            if self.get_user_input():
                break
            self.user_input_publisher.publish(self.data)
            self.get_logger().info(f'Current data:\n\tspeed:{self.data.y_speed}\n\tangle:{self.data.x_angle}')

    def get_user_input(self):
        command = input('Enter command (w/a/s/d, q to quit): ')
        if command == 'w' or command == 's':
            new_speed = self.data.y_speed
            new_speed += self.SPEED_INCREMENT if command == 'w' else -self.SPEED_INCREMENT
            if abs(new_speed) > self.MAX_Y_SPEED:
                self.get_logger().warning('Speed limit reached') 
            self.data.y_speed = min(abs(new_speed), self.MAX_Y_SPEED) * new_speed / abs(new_speed)
            return False

        if command == 'a' or command == 'd':
            new_angle = self.data.x_angle
            new_angle += self.ANGLE_INCREMENT if command == 'a' else -self.ANGLE_INCREMENT
            if abs(new_angle) > self.MAX_X_ANGLE:
                self.get_logger().warning('Angle limit reached') 
            self.data.x_angle = min(abs(new_angle), self.MAX_X_ANGLE) * new_angle / abs(new_angle)

            return False

        if command == 'q':
            return True

def main(args=None):
    rclpy.init(args=args)
    node = GamepadPublisher()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
