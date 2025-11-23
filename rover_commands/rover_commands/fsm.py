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


class FSMNode(Node, State):

    subscribers = {}
    move_delta = MoveData()

    def __init__(self):
        super().__init__('fsm_node')

        try:
            self.add_subscription(
                MoveData,
                'user_input',
                lambda msg: self.__call__(
                    'user_input_sub_callback',
                    msg
                ),
                default_data = MoveData()
            )
        except:
            ...

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
        if msg.speed == 3:
            self.__switch_state__('SyncState')
        if msg.speed == 5:
            self.__switch_state__('FailState')

class OKState(FSMNode):
    ...

class SyncState(FSMNode):
    ...

class FailState(FSMNode):
    def __init__(self):
        print('NOPE')
        rclpy.shutdown()

def main(args=None):

    rclpy.init(args=args)

    FSM = StateMachine(
        ['subscribers', 'move_delta'],
        ['add_subscription', 'user_input_sub_callback']
    ) \
        .add_state(OKState) \
        .add_state(SyncState) \
        .add_state(FailState)

    FSM.spin('OKState')

    rclpy.spin(FSM.active)
    FSM.active.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
