import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData


class GamePadPublisher(Node):
    user_input_pub = None
    data = MoveData()
    
    MAX_SPEED = 255
    MAX_ANGLE = 90

    SPEED_INCREMENT = 50.0
    ANGLE_INCREMENT = 10.0

    def __init__(self):

        super().__init__('gamepad')

        self.user_input_pub = self.create_publisher(MoveData, 'user_input', 10) 
        self.get_logger().info('[GAMEPAD] Publisher node has been started.')

        while True:
            if self.cmd_acquisition():
                break
            self.user_input_pub.publish(self.data)
            self.get_logger().info(f'Current data:\n\tspeed:{self.data.speed}\n\tangle:{self.data.angle}')

    def cmd_acquisition(self):
        command = input('Enter command (w/a/s/d, q to quit): ')
        if command == 'w':
            new_speed = self.data.speed + self.SPEED_INCREMENT
            if new_speed > self.MAX_SPEED:
                self.get_logger().warning('Maximal speed reached') 
            self.data.speed = min(new_speed, self.MAX_SPEED)
            return False
        if command == 's':
            if self.data.speed > self.MIN_SPEED:
                self.data.speed -= 50.0
            else:
                self.get_logger().warning('Minimal speed reached') 
            return False
        if command == 'a':
            if self.data.angle > self.MIN_ANGLE:
                self.data.angle -= 10.0
            else:
                self.get_logger().warning('Minimal angle reached') 
            return False
        if command == 'd':
            if self.data.angle < self.MAX_ANGLE:
                self.data.angle += 10.0
            else:
                self.get_logger().warning('Maximal angle reached') 
            return False
        if command == 'q':
            return True


def main(args=None):
    rclpy.init(args=args)
    node = GamePadPublisher()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
