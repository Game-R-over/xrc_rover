import rclpy
from rclpy.node import Node
from custom_msg.srv import CheckPosition

class CheckPositionServer(Node):

    def __init__(self):
        super().__init__('check_position_server')
        self.srv = self.create_service(
            CheckPosition,
            'check_position',
            self.check_position_callback
        )

        self.get_logger().info('Service server has been started.')

    def check_position_callback(self, request, response):
        response.is_allowed = not (abs(request.x) > 100 or abs(request.z) > 100)
        response.suggestion = "Position is within the safe zone"
        # TODO - BONUS: Try to give a recommendation of which move would help moving further away from the boundaries if you are too close to a boundary.
        # Your code here

        x = request.x
        z = request.z
        self.get_logger().info(f'Received request: x={x}, z={z}')
        self.get_logger().info(f'Response: is_allowed={response.is_allowed}, suggestion="{response.suggestion}"')
        return response

def main(args=None):
    rclpy.init(args=args)
    node = CheckPositionServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
