import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class TrajectoryPublisher(Node):

    def __init__(self):
        super().__init__('trajectory_publisher')

        self.publisher_ = self.create_publisher(Twist, 'position', 10) # a queue size of 10 usually works!
        self.get_logger().info('Publisher node has been started.')

        while True:
            cmd = self.cmd_acquisition()
            self.publisher_.publish(cmd)


    # Function that prompts user for a direction input, and sends the command
    def cmd_acquisition(self):
        command = input('Enter command (w/a/s/d/t/y - max 2 characters): ')
        cmd = Twist()
        if command == "w":
            cmd.linear.x = 1.0
            return cmd
        if command == "a":
            cmd.linear.z = -1.0
            return cmd
        if command == "s":
            cmd.linear.x = -1.0
            return cmd
        if command == "d":
            cmd.linear.z = 1.0
            return cmd
        if command == "t":
            cmd.angular.y = 1.0
            return cmd
        if command == "y":
            cmd.linear.y = -1.0
            return cmd
        return cmd

def main(args=None):
    rclpy.init(args=args)   # Init ROS python
    node = TrajectoryPublisher()  # Create a Node instance
    rclpy.spin(node)  # Run the node in a Thread
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
