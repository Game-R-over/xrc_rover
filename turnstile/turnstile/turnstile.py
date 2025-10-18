import rclpy
from rclpy.node import Node

from custom_msg.msg import OperateTurnstile
from turnstile.FiniteStateMachine import State, StateMachine

class OpenTurnstile(State):
    times_opened = 0
    def coin(self):
        pass
    def push(self):
        return { '__NEW_STATE__': 'ClosedTurnstile' }

class ClosedTurnstile(State):
    times_opened = 0
    def coin(self):
        self.times_opened += 1
        return { '__NEW_STATE__': 'OpenTurnstile' }
    def push(self):
        pass

class Turnstile(Node):

    def __init__(self):
        super().__init__('turnstile')
        self.subscription = self.create_subscription(
            OperateTurnstile,
            'turnstile_topic',
            self.listener_callback,
            10
        )

        self.fsm = StateMachine(['times_opened'], ['coin', 'push']).add_state(OpenTurnstile).add_state(ClosedTurnstile)
        self.fsm.spin('ClosedTurnstile')

    def listener_callback(self, msg):
        if msg.action:
            self.fsm.call('push')
        else:
            self.fsm.call('coin')
        self.get_logger().info(f'State is now: {self.fsm.active.repr()}')
        self.get_logger().info(f'Turnstile has been opened {self.fsm.active.times_opened} times')

def main(args=None):
    rclpy.init(args=args)

    sub = Turnstile()

    rclpy.spin(sub)

    sub.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
