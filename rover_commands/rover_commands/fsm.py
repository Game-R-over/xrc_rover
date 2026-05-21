from .fsm_lib.fsm import StateMachine, State

import rclpy
from rclpy.node import Node

from std_msgs.msg import Empty
from custom_msg.msg import MoveData

class FSMNode(Node):
    def __init__(self, fsm: StateMachine):
        super().__init__('fsm_node')
        self.fsm = fsm
        fsm.goal = None

        self.move_pub = self.create_publisher(MoveData, 'move_update', 10)
        self.shutdown_pub = self.create_publisher(Empty, 'emergency_shutdown', 10)

        self.create_subscription(
            MoveData,
            'user_input',
            self.user_input_callback,
            10
        )

        self.get_logger().info("FSM Node started")

    def user_input_callback(self, msg: MoveData):
        event = {
            "type": "user_input",
            "data": msg
        }

        self.fsm.dispatch(event)

    def publish(self, topic: str, msg):
        if topic == "move_update":
            self.move_pub.publish(msg)

        elif topic == "emergency_shutdown":
            self.shutdown_pub.publish(msg)

class ManualState(State):
    def on_event(self, fsm, event):

        if event["type"] == "emergency":
            fsm.transition("FAIL")

        if event["type"] == "user_input":
            msg = event["data"]

            fsm.publish("move_update", msg)

            if msg.y_speed == 200:
                fsm.transition("FAIL")

class AutomaticState(State):
    def on_event(self, fsm, event):

        if event["type"] == "emergency":
            fsm.transition("FAIL")

        if event["type"] == "obstacle":
            if event["severity"] > 5:
                # TODO: Add stop_cmd()
                fsm.publish("move_update", stop_cmd())
                return

            if event["distance"] < 0.8:
                cmd = self.avoid_vector(event)
                fsm.publish("move_update", cmd)
                return

        if event["type"] == "aruco":
            fsm.goal = (event["x"], event["y"])
            cmd = self.go_to_target()
            fsm.publish("move_update", cmd)
            return

        if event["type"] == "user_input":
            ...

    def avoid_vector(obstacle):
        strength = 1.0 / (obstacle["distance"] + 0.1)

        return {
            "linear_x": 0.2,
            "angular_z": -obstacle["angle"] * strength
        }

    def go_to_target():
        return {
            "linear_x": 0.5,
            "angular_z": -0.8 * fsm.goal[1]
        }

class FailState(State):
    def on_enter(self, fsm):
        fsm.publish("emergency_shutdown", Empty())

    def on_event(self, fsm, event):
        ...

class BootingState(State):
    def on_enter(self, fsm):
        fsm.transition("MANUAL")

def main(args=None):
    rclpy.init(args=args)

    fsm = StateMachine()

    fsm.add_state("BOOT",   BootingState())
    fsm.add_state("MANUAL", ManualState())
    fsm.add_state("AUTO",   AutomaticState())
    fsm.add_state("FAIL",   FailState())

    fsm.set_initial("MANUAL")

    node = FSMNode(fsm)

    # inject ROS publish function into FSM
    fsm.publish = node.publish

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()
