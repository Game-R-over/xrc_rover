import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from geometry_msgs.msg import PoseStamped
from rclpy.qos import qos_profile_sensor_data
import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R

class ArucoDetectorNode(Node):
    def __init__(self):
        super().__init__('aruco_detector')
        
        self.image_sub = self.create_subscription(
            CompressedImage,
            '/camera/image_raw/compressed',
            self.image_callback,
            qos_profile_sensor_data
        )
        
        # Publisher for the EKF Node
        self.pose_pub = self.create_publisher(PoseStamped, '/vision/pose', 10)
        
        self.marker_size = 0.137
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
        half_size = self.marker_size / 2.0
        self.obj_points = np.array([
            [-half_size,  half_size, 0],
            [ half_size,  half_size, 0],
            [ half_size, -half_size, 0],
            [-half_size, -half_size, 0]
        ], dtype=np.float32)

        self.get_logger().info('ArUco Detector Node initialized (EKF Compatible).')

    def get_generic_camera_matrix(self, width, height):
        focal_length = width * 0.8
        center_x = width / 2.0
        center_y = height / 2.0
        return np.array([
            [focal_length, 0, center_x],
            [0, focal_length, center_y],
            [0, 0, 1]
        ], dtype=np.float32)

    def image_callback(self, msg):
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return
            
        height, width = frame.shape[:2]
        corners, ids, rejected = self.detector.detectMarkers(frame)
        
        camera_matrix = self.get_generic_camera_matrix(width, height)
        dist_coeffs = np.zeros((4,1))
        
        if ids is not None and len(ids) > 0:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            for i in range(len(ids)):
                success, rvec, tvec = cv2.solvePnP(
                    self.obj_points, 
                    corners[i], 
                    camera_matrix, 
                    dist_coeffs, 
                    flags=cv2.SOLVEPNP_IPPE_SQUARE
                )
                
                if success:
                    # Draw axes for visualization (OpenCV frame)
                    cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvec, tvec, self.marker_size / 2)
                    
                    # Convert from OpenCV optical frame to ROS base_link frame conventions
                    # OpenCV: Z forward, X right, Y down
                    # ROS: X forward, Y left, Z up
                    
                    # 1. Get the Marker's pose in the Camera frame
                    x_cam = tvec[0][0]
                    y_cam = tvec[1][0]
                    z_cam = tvec[2][0]
                    
                    # Convert translation to ROS conventions
                    x_ros = z_cam
                    y_ros = -x_cam
                    z_ros = -y_cam
                    
                    # Convert rotation to ROS conventions
                    rmat, _ = cv2.Rodrigues(rvec)
                    
                    # Construct rotation matrix for the axis swap
                    # R_ros_cam maps Camera Optical Frame to ROS Camera Link
                    R_ros_cam = np.array([
                        [ 0,  0,  1],
                        [-1,  0,  0],
                        [ 0, -1,  0]
                    ], dtype=np.float64)
                    
                    # Rotate the marker's orientation into the ROS frame
                    rmat_ros = np.dot(R_ros_cam, rmat)
                    
                    # If the EKF expects the robot's global pose (Robot relative to Marker):
                    # We invert the ROS transform. T_robot = T_marker^-1
                    rmat_robot = rmat_ros.T
                    tvec_robot = -np.dot(rmat_robot, np.array([x_ros, y_ros, z_ros]))
                    
                    rotation = R.from_matrix(rmat_robot)
                    quat = rotation.as_quat() # [x, y, z, w]
                    
                    pose_msg = PoseStamped()
                    pose_msg.header.stamp = msg.header.stamp
                    pose_msg.header.frame_id = "map"
                    
                    # Publish the Robot's pose relative to the Marker
                    pose_msg.pose.position.x = float(tvec_robot[0])
                    pose_msg.pose.position.y = float(tvec_robot[1])
                    pose_msg.pose.position.z = float(tvec_robot[2])
                    
                    pose_msg.pose.orientation.x = float(quat[0])
                    pose_msg.pose.orientation.y = float(quat[1])
                    pose_msg.pose.orientation.z = float(quat[2])
                    pose_msg.pose.orientation.w = float(quat[3])
                    
                    self.pose_pub.publish(pose_msg)
        
        # Display the frame
        cv2.imshow("ArUco Detector", frame)
        cv2.waitKey(1)

def main():
    rclpy.init()
    node = ArucoDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
