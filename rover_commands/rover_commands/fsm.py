from .fsm_lib.fsm import StateMachine, State

import rclpy
from rclpy.node import Node

from std_msgs.msg import Empty
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

class FSMNodePublisher:
    publisher = None

    def __init__(self, create_pub_callback, datatype, topic, queue_size = 10):
        self.publisher = create_pub_callback(
            datatype,
            topic,
            queue_size
        )

class FSMNode(Node, State):

    subscribers = {}
    publishers = {}

    def __init__(self):
        super().__init__('fsm_node')

        self.get_logger().info('[FSMNode] User input subscriber node has been started.')

    def add_subscription(self, datatype, topic, callback, queue_size = 10, default_data = None):
        if topic in self.subscribers:
            raise ValueError(f'Trying to add already existing subscriber {topic}.')

        self.subscribers[topic] = FSMNodeSubscriber(
            self.create_subscription,
            datatype,
            topic,
            callback,
            queue_size,
            default_data
        )

    def add_publisher(self, datatype, topic, queue_size = 10):
        if topic in self.publishers:
            raise ValueError(f'Trying to add already existing publisher {topic}.')

        self.publishers[topic] = FSMNodePublisher(
            self.create_publisher,
            datatype,
            topic,
            queue_size
        )

    def user_input_sub_callback(self, msg):
        # Do nothing (overriden in ManualState and AutomaticState)
        ...

class BootingState(FSMNode):
    ...

class ManualState(FSMNode):
    def user_input_sub_callback(self, msg):
        self.get_logger().info(f'User Input: {msg.speed}, {msg.angle}')
        self.subscribers['user_input'].data = msg
        self.publishers['move_update'].publisher.publish(msg)

        # TODO: Remove this test
        if msg.speed == 200:
            self.get_logger().warning('Shutting down FSM')
            self.__switch_state__('FailState')

class AutomaticState(FSMNode):
    def user_input_sub_callback(self, msg):
        self.get_logger().info(f'[IGNORED] User Input: {msg.speed}, {msg.angle} in automatic state.')

class FailState(FSMNode):
    def __init__(self):
        super().__init__()
        self.publishers['emergency_shutdown'].publisher.publish(Empty())

    def user_input_sub_callback(self, msg):
        self.get_logger().info(f'[IGNORED] User Input: {msg.speed}, {msg.angle} in fail state.')

def main(args=None):

    rclpy.init(args=args)

    FSM = StateMachine(
        ['subscribers', 'publishers'],
        ['add_subscription', 'user_input_sub_callback']
    ) \
        .add_state(BootingState) \
        .add_state(ManualState) \
        .add_state(AutomaticState) \
        .add_state(FailState)

    FSM.spin('BootingState')
    FSM.call(
        'add_subscription',
        MoveData,
        'user_input',
        lambda msg: FSM.call(
            'user_input_sub_callback',
            msg
        ),
        default_data = MoveData()
    )
    FSM.call(
        'add_publisher',
        MoveData,
        'move_update'
    )
    FSM.call(
        'add_publisher',
        Empty,
        'emergency_shutdown'
    )

    rclpy.spin(FSM.active)

    FSM.active.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
