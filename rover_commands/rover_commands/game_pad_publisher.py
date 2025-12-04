import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData


class GamePadPublisher(Node):
    user_input_pub = None
    data = MoveData()
    
    MAXSPEED=10
    MAXANGLE=10

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
           if self.data.speed< self.MAXSPEED:
               self.data.speed += 1.0
           else:
               self.get_logger().info('maximal speed reached') 
           return False
       if command == 's':
           if self.data.speed >0:
               self.data.speed -= 1.0
           else:
               self.get_logger().info('minimal speed reached') 
           return False
       if command == 'a':
           if self.data.angle>0:
               self.data.angle -= 1.0
           else:
               self.get_logger().info('minimal angle reached') 
           return False
       if command == 'd':
           if self.data.angle<self.MAXANGLE:
               self.data.angle += 1.0
           else:
               self.get_logger().info('maximal angle reached') 
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
