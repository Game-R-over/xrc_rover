import rclpy
from rclpy.node import Node

from custom_msg.msg import ServoAngle, Vec2
from std_msgs.msg import Empty, Int32

from .utils.arm import ArmData

class ArmManager(Node):

    subscribers = {
        'arm_position_update': None,
        'arm_angle_update': None,
        'arm_claw_update': None,
    }

    publishers = {
        'servo_angle_update': None,
    }

    data = {
        'servo_angle_update': ServoAngle(),
    }

    CLAW_SERVO = 1
    ARM_SERVOS = (2, 3)
    BASE_SERVO = 4

    arm = ArmData()

    def __init__(self):
        super().__init__('arm_manager')

        self.subscribers['arm_position_update'] = self.create_subscription(
            Vec2,
            'arm_position_update',
            self.arm_position_update_listener_callback,
            10
        )
        self.subscribers['arm_angle_update'] = self.create_subscription(
            Int32,
            'arm_angle_update',
            self.arm_angle_update_listener_callback,
            10
        )
        self.subscribers['emergency_shutdown'] = self.create_subscription(
            Empty,
            'emergency_shutdown',
            self.emergency_shutdown_listener_callback,
            10
        )

        self.publishers['servo_angle_update'] = self.create_publisher(
            ServoAngle,
            'servo_angle_update',
            10
        )

        self.get_logger().info('[START]')

    def arm_position_update_listener_callback(self, msg):
        arm.computeAngles(
            Vec2(msg.x, msg.y)
        )
        for i in range(len(self.ARM_SERVOS)):
            self.data['servo_angle_update'].angle = arm.angles[i]
            self.data['servo_angle_update'].servo = self.ARM_SERVOS[i]
            self.publish('servo_angle_update')

    def arm_angle_update_listener_callback(self, msg):
        self.data['servo_angle_update'].angle = msg.data
        self.data['servo_angle_update'].servo = self.BASE_SERVO
        self.publish('servo_angle_update')



    def emergency_shutdown_listener_callback(self, msg):
        for i in list(self.ARM_SERVOS) + [self.CLAW_SERVO, self.BASE_SERVO]:
            self.data['servo_angle_update'].angle = 0
            self.data['servo_angle_update'].servo = i + self.SERVOS_OFFSET
            self.publish('servo_angle_update')

        self.get_logger().info('Sending shutdown speed to ESP')

    def publish(self, topic):
        self.publishers[topic].publish(self.data[topic])

def main(args=None):
    rclpy.init(args=args)
    node = ArmManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
