import rclpy
from rclpy.node import Node
from custom_msg.msg import MoveData


class GamePadPublisher(Node):
    user_input_pub=None
    data=None
    def __init__(self):

        super().__init__('game_pad')

        self.user_input_pub = self.create_publisher(MoveData, 'user_input', 10) 
        # a queue size of 10 usually works!
        self.get_logger().info('Publisher node has been started.')
        data = MoveData()
        while True:
            cmd = self.cmd_acquisition(data)
            self.user_input_pub.publish(cmd)
            self.get_logger().info(f'speed:{data.speed} angle:{data.angle}')
            
            #interdit publish none


    # Function that prompts user for a direction input, and sends the command
    def cmd_acquisition(self,data ):
        command = input('Enter command (w/a/s/d/t/y - max 2 characters): ')
        if command == "w":
            data.speed += 1.0
            return data
        if command == "a":
            data.speed -= 1.0
            return data
        if command == "s":
           data.angle -= 1.0
           return data
        if command == "d":
            data.angle += 1.0
            return data
        return data


def main(args=None):
    rclpy.init(args=args)   # Init ROS python
    node = GamePadPublisher()  # Create a Node instance
    rclpy.spin(node)  # Run the node in a Thread
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
