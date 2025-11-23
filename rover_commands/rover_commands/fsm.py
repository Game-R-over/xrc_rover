from .fsm_lib.fsm import StateMachine, State

import rclpy
from rclpy.node import Node

from custom_msg.msg import MoveData

class FSMNodeSubscriber:
    subscription = None
    data = None

    def __init__(self, create_sub_callback, datatype, topic, callback, queue_size = 10, default_data = None):
        self.data = default_data
        self.subscription = create_sub_callback(
            datatype,
            topic,
            callback,
            queue_size
        )


class FSMNode(Node):

    subscribers = {}
    move_delta = MoveData()

    def __init__(self):
        super().__init__('fsm_node')

        self.add_subscription(
            MoveData,
            'user_input',
            self.user_input_sub_callback,
            default_data = MoveData()
        )

        self.get_logger().info('[FSMNode] User input subscriber node has been started.')

    def add_subscription(self, datatype, topic, callback, queue_size = 10, default_data = None):
        if topic in self.subscribers:
            raise ValueError(f'Trying to add already existing subscriber {topic}.')

        self.subscribers[topic] = (FSMNodeSubscriber(
            self.create_subscription,
            datatype,
            topic,
            callback,
            queue_size,
            default_data
        ))

    def user_input_sub_callback(self, msg):
        self.get_logger().info(f'Response: {msg.speed}, {msg.angle}')
        self.move_delta.speed = msg.speed - self.subscribers['user_input'].data.speed 
        self.move_delta.angle = msg.angle - self.subscribers['user_input'].data.angle
        self.subscribers['user_input'].data = msg
        self.get_logger().info(f'Delta : {self.move_delta.speed}, {self.move_delta.angle}')

def main(args=None):
    rclpy.init(args=args)
    node = FSMNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
