import rclpy
from rclpy.node import Node
from custom_msg.msg import UltrasonicDistance
from std_msgs.msg import Empty


class Ultrasonics(Node):
    DANGER_THRESHOLD= 0.30

    def __init__(self):
        super().__init__('ultrasonics_node')

        self.ultrasonic_suscriber= self.create_subscription(
            UltrasonicDistance,
            '/ultrasonic_distance_feedback',
            self.ultrasonic,
            10
        )
        
        self.ultrasonic_alert_publisher= self.create_publisher(Empty, 'alert_fsm', 10)

    def ultrasonic(self, msg): 
        if msg.distance <  self.DANGER_THRESHOLD:
            self.ultrasonic_alert_publisher.publish(Empty())
            self.get_logger().warn(
                    f'DANGER détecté sur {msg.sensor} : {msg.distance:.3f} m'
                )

   

def main():
    rclpy.init()
    node = Ultrasonics()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()



