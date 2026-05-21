# ROS2 6-Wheel Rover + Nav2 + EKF Context Export

## Project Goal

Build a ROS2-based autonomous 6-wheel rover using:

* Custom wheel odometry
* IMU fusion
* Custom EKF localization
* Nav2
* TF tree
* URDF/Xacro robot model
* Optional camera/Aruco localization

The rover:

* Has 6 driven wheels
* Front + rear steering
* Middle wheels fixed
* Publishes wheel speeds and steering angles
* Uses custom kinematic least-squares odometry

The user wants to:

* Use THEIR OWN EKF implementation
* NOT use robot_localization
* Eventually integrate with Nav2 properly

---

# Current Architecture Direction

The system architecture SHOULD become:

wheel sensors
↓
wheel odometry node
↓
publish twist-only odom
↓
custom EKF node
↓
publish fused localization
↓
Nav2

---

# Important Design Decision

The wheel odometry node should:

✔ Compute:

* vx
* vy
* omega

✔ Publish:

* nav_msgs/Odometry

BUT:

❌ should NOT:

* integrate global pose
* estimate x/y/theta
* publish TF
* own localization

The EKF node should:

* fuse wheel odometry + IMU (+ optional vision)
* estimate global pose
* publish TF
* publish /odometry/filtered

---

# TF Structure

Desired TF tree:

map
└── odom
└── base_footprint
└── base_link
├── wheels
├── imu_link
├── camera_link
└── arm links

Important:

* base_footprint is planar
* base_link may contain roll/pitch
* wheel odometry publishes:
  header.frame_id = "odom"
  child_frame_id = "base_footprint"

The EKF will later publish:

* odom → base_footprint TF

---

# Current URDF Notes

The user already added:

* base_link
* base_footprint
* steering wheel joints
* arm links
* imu_link
* camera_link

Steering wheels:

* steer_wheel_fl
* steer_wheel_fr
* steer_wheel_bl
* steer_wheel_br

Wheel joints:

* continuous wheel rotation joints

The issue:

* robot_state_publisher only publishes transforms for joints that receive JointState messages.

The user initially saw:
"No transform from arm_planar_frame to base_link"

Cause:

* revolute joints existed but no joint states were being published.

Solution:

* either publish joint states
* or temporarily make joints fixed

---

# Wheel Odometry Kinematics

The wheel odometry computes body twist using least-squares constraints.

Core output:
[vx, vy, omega]

The solver uses:

* rolling constraints
* no-slip constraints

The user's compute_speeds() is considered good and should be kept.

---

# IMPORTANT REFACTOR

The wheel odometry node was refactored conceptually into:

PURE TWIST ESTIMATOR

Meaning:

* no State class
* no quaternion generation
* no pose integration
* no TF broadcasting

Only:

* compute local twist
* publish Odometry twist

Pose in Odometry should be dummy/unknown with huge covariance.

---

# Recommended Wheel Odometry Output

Topic:
/odom/wheel

Message:
nav_msgs/Odometry

Frames:
header.frame_id = "odom"
child_frame_id = "base_footprint"

Pose:

* identity
* meaningless
* huge covariance

Twist:

* vx
* vy
* omega
* useful covariance

---

# EKF Discussion

The user initially had:

state:
[x, y, theta, v, b]

where:

* v = forward velocity
* b = gyro bias

The user asked whether to use:
[x, y, theta, vx, vy, b]

Answer:
YES

Reason:

* rover supports lateral motion
* steering rover is NOT differential drive
* Nav2 expects full planar motion
* vx/vy better represent holonomic behavior

The gyro bias b should remain because:

* IMU omega will be fused
* MEMS gyros drift
* EKF can estimate bias online

Recommended state:
[x, y, theta, vx, vy, b]

---

# Current EKF Code

The user already has a custom EKF class with:

* predict()
* update()
* Jacobians
* covariance propagation

The EKF currently assumes:
[x, y, theta, v, b]

It will need refactoring to:
[x, y, theta, vx, vy, b]

The EKF should:

* subscribe to /odom/wheel
* subscribe to /imu
* optionally subscribe to Aruco pose
* publish:
  /odometry/filtered
* broadcast TF:
  odom → base_footprint

---

# Important Guidance Given

The wheel odometry node should become:
"wheel kinematics only"

NOT:
"wheel odometry + localization"

This separation is important for Nav2.

---

# Current Recommended Wheel Odometry Node Structure

The latest recommendation was:

* remove:
  State class
  update_state()
  send_tf_transform()
  quaternion generation
  integrated pose

* keep:
  compute_speeds()

* publish:
  Odometry with:
  meaningful twist
  meaningless pose

---

# Package / Environment Notes

The user had trouble installing:

* joint_state_publisher
* joint_state_publisher_gui

Likely because:

* incorrect ROS distro
* missing apt sources

No resolution yet.

---

# User Skill/Project Context

The user:

* understands ROS2 reasonably well
* writes custom kinematics
* writes custom EKFs
* wants full control over localization
* is building a serious rover stack
* is not looking for beginner shortcuts

Avoid:

* oversimplified "just use robot_localization"
* replacing custom EKF with stock packages

Instead:

* help integrate the custom stack cleanly into ROS2/Nav2 architecture.

---

```json
{
  "project": "outdoor_rover_nav2",
  "robot": {
    "type": "6wd_steered_rover",
    "drive": "6_wheel_drive",
    "steering": {
      "front": "steering",
      "rear": "steering",
      "middle": "fixed"
    },
    "kinematics": "non_differential_ackermann_like_extended"
  },

  "ros_stack": {
    "ros_version": "ROS2",
    "nav2": true,
    "nav2_role": "trajectory_planning_and_cmd_vel_generation",
    "tf_tree": [
      "map -> odom -> base_footprint -> base_link"
    ]
  },

  "state_estimation": {
    "ekf": {
      "custom": true,
      "implementation_language": "python",
      "state_vector": ["x", "y", "theta", "vx", "vy", "omega", "bias"],
      "inputs": [
        "wheel_odometry (/odom/wheel)",
        "imu (/imu/data)",
        "vision_arcuo (/vision/pose)"
      ],
      "outputs": [
        "/odometry/filtered",
        "tf odom->base_footprint"
      ],
      "design_question": "whether aruco should be fused in local EKF or separate global localization layer"
    },

    "localization_architecture_options": {
      "option_A_current": "single_EKF_fusing_vision+imu+wheel -> global_pose_inferred",
      "option_B_recommended": {
        "ekf_local": "wheel+imu -> odom->base",
        "global": "aruco -> map->odom"
      }
    }
  },

  "nav2_integration": {
    "input": "/cmd_vel",
    "output": "nav2_plans_velocity_commands",
    "requirements": [
      "stable_odom_frame",
      "consistent_tf_tree",
      "low_latency_odometry"
    ]
  },

  "robot_control_architecture": {
    "decision": "NO_ros2_control_required_initially",
    "reason": "rapid_iteration_and_custom_kinematics_needed",

    "future_option": {
      "ros2_control_possible": true,
      "benefits": [
        "joint_state_management",
        "tf_consistency",
        "hardware_abstraction"
      ]
    },

    "current_pipeline": [
      "nav2_cmd_vel",
      "custom_kinematics_controller",
      "motor_interface"
    ]
  },

  "step3_kinematics_controller": {
    "role": "cmd_vel_to_actuators",
    "inputs": {
      "linear_x": "v",
      "angular_z": "omega"
    },

    "outputs": {
      "wheel_velocities": 6,
      "steering_angles": 4
    },

    "model": {
      "base_model": "bicycle_model_extended",
      "wheelbase": "L",
      "equations": {
        "turning_radius": "R = v / omega",
        "steering_angle": "delta = atan(L * omega / v)",
        "wheel_speed": "omega_wheel = v / r"
      }
    },

    "steering_modes": [
      "counter_steering (front=+delta, rear=-delta) RECOMMENDED",
      "crab_steering (front=rear=delta)",
      "front_only_steering (rear=0)"
    ],

    "safety_requirements": [
      "steering_limit_clamp",
      "steering_rate_limiting",
      "low_speed_rotation_handling"
    ]
  },

  "urdf_role": {
    "purpose": "geometry_and_tf_only",
    "not_responsible_for": [
      "motion_logic",
      "cmd_vel_handling",
      "kinematics"
    ]
  },

  "open_design_questions": [
    "should EKF include ArUco or separate localization layer",
    "exact steering coupling model for front+rear steering",
    "whether to introduce ros2_control later",
    "final wheel speed distribution model (simple vs slip-aware)"
  ]
}
```

---

Project context:

* Student rover competition with 5 tasks:

  1. Autonomous path-finding using ArUco target + obstacle avoidance + optional object pickup/return
  2. Remote navigation/teleop through terrain
  3. Manipulation/object collection
  4. Race
  5. Collaborative multi-rover task

Current rover sensors:

* 9-axis IMU
* monocular camera
* wheel encoders
* steering servo angles
* ultrasonic sensors (used ONLY for emergency stop)
* camera stack:

  * MiDaS for monocular relative depth
  * YOLO for object detection
  * ArUco detection

Current localization:

* EKF fusing:

  * wheel odometry
  * IMU gyro + magnetometer
  * ArUco corrections

Important conclusions reached:

1. MiDaS DOES NOT provide metric depth.

   * It only provides relative depth.
   * Therefore we should NOT build a fake metric occupancy map from MiDaS.

2. Instead of metric SLAM, the recommended architecture is:

   * local traversability map
   * sparse semantic/global memory
   * reactive navigation

3. Initial “LEFT/CENTER/RIGHT sectors” suggestion was intentionally simplified.

   * Better architecture is:
     camera image
     → MiDaS depth field
     → ground-plane projection
     → local traversability grid

4. Traversability map should:

   * be local and rolling (3–5m around rover)
   * be centered on rover
   * use:

     * MiDaS geometry
     * YOLO semantic labels
     * ultrasonic emergency overrides

5. Recommended map representation:
   grid[x][y] = traversability_score
   NOT occupancy probability.

6. ArUco is the ONLY reliable metric anchor.
   Use ArUco for:

   * target pose
   * return alignment
   * pickup alignment

7. Recommended autonomy architecture:
   Sensors
   ↓
   Perception:

   * YOLO
   * MiDaS
   * ArUco
     ↓
     Fusion:
   * EKF
   * traversability map
     ↓
     Planner:
   * reactive/vector-field local planner
     ↓
     FSM
     ↓
     Motion control

FSM discussion:

* Original FSM implementation used:

  * threading.Timer
  * class mutation via setattr
  * ROS node inheritance inside states
  * hidden dispatch methods
  * direct publisher/subscriber ownership in states

* Recommendation:
  DO NOT rewrite ROS-like runtime from scratch.
  Keep ROS2 as runtime/executor.
  Simplify FSM into pure deterministic event-driven logic.

Final FSM architecture:

* ROS node handles:

  * publishers
  * subscribers
  * timers
  * ROS callbacks
* FSM handles:

  * state transitions
  * event routing
  * decision logic only

Recommended FSM structure:

```py
class State:
    def on_enter(self, fsm): ...
    def on_exit(self, fsm): ...
    def on_event(self, fsm, event): ...
```

```py
class StateMachine:
    def add_state(...)
    def set_initial(...)
    def transition(...)
    def dispatch(event)
```

Events should be normalized dicts like:

```py
{
    "type": "aruco",
    "distance": 2.1,
    "yaw": -0.1
}
```

```py
{
    "type": "obstacle",
    "risk": 0.82,
    "angle": 0.3
}
```

Updated ROS architecture:

* single ROS node
* ROS callbacks convert messages → events
* FSM dispatches events
* FSM outputs commands via injected publish function

Key robotics conclusions:

* Avoid trying full metric SLAM with current sensors.
* Build:

  * local geometric traversability map
  * sparse world memory
  * reactive planner
* Determinism and robustness are more important than sophistication for this competition.

Potential next discussion topics:

* actual traversability grid implementation
* ground-plane projection from monocular camera
* vector-field navigation
* ArUco return-home logic
* object pickup FSM
* costmap/traversability scoring
* ROS2 node graph
* EKF confidence integration

---

# Conversation Continuation Summary

## 1. Primary Objective

The user is building a **mobile manipulator rover** (rover base + robotic arm) using ROS and wants to:

* Use an existing **URDF** of the rover + arm with **MoveIt** for motion planning.
* Install and configure MoveIt properly.
* Eventually perform arm motion planning and likely integrate the rover base later.

### Current Progress Stage

The conversation reached:

* Conceptual setup for using MoveIt with the rover URDF
* Step-by-step installation instructions for **MoveIt 2 on ROS 2 Humble**
* Guidance on how to structure the MoveIt setup process

The user has **not yet provided the URDF** or specific hardware/software stack details beyond wanting to use MoveIt.

---

# 2. Key Facts and Context

## Assumed Environment

The guidance assumed:

* Ubuntu 22.04
* ROS 2 Humble
* MoveIt 2
* RViz2
* ros2_control
* colcon workspace
* Xacro/URDF workflow

### Suggested Workspace

```bash
~/ws_moveit

with packages like:

my_rover_description/
my_rover_moveit_config/
Rover Architecture Assumption

The rover has:

base_link
 ├── wheels
 └── arm_base_link
      └── arm chain

The arm is mounted to the rover body.

Important Strategic Recommendation

The user was strongly advised to:

START WITH:
Fixed-base arm planning only
NOT:
Whole-body rover + arm planning initially

Reason:

Much simpler debugging
Faster planning
Easier IK and collision handling
More stable MoveIt setup
Suggested Long-Term Architecture

Recommended eventual architecture:

Nav2 handles rover navigation
MoveIt handles arm manipulation
Higher-level task planner coordinates both

This was recommended over MoveIt whole-body planning.

3. Decisions Already Made
Finalized Recommendations
Use:
ROS 2 Humble
MoveIt 2
ros2_control
RViz2
OMPL planners
Initial MoveIt setup:
Arm-only planning group

Fixed virtual joint:

world -> base_link
type: fixed
Planning group:

Only arm joints.

Avoid initially:
Planning wheel motion in MoveIt
Planar virtual joints
Whole-body planning
Explicitly Rejected / Deferred
Whole-body planning

Deferred because:

Harder controller integration
More difficult OMPL tuning
Slower planning
More debugging complexity
Planar mobile-base MoveIt setup

Deferred until arm-only planning works reliably.

4. Work Completed
High-Level MoveIt Workflow Explained

The assistant explained:

Validate URDF
Launch MoveIt Setup Assistant
Generate collision matrix
Create planning groups
Configure controllers
Generate MoveIt package
Launch RViz + MoveIt
Test planning
Use MoveGroup APIs
Installation Instructions Provided

Detailed install steps were given for:

ROS setup
source /opt/ros/humble/setup.bash
MoveIt install
sudo apt update
sudo apt install ros-humble-moveit
ros2_control
sudo apt install \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-joint-trajectory-controller
Utility packages
sudo apt install \
  ros-humble-xacro \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-tf2-tools \
  ros-humble-rviz2
Workspace setup
mkdir -p ~/ws_moveit/src
cd ~/ws_moveit
colcon build
source install/setup.bash
Launch Setup Assistant
ros2 launch moveit_setup_assistant setup_assistant.launch.py
Panda example test
sudo apt install ros-humble-moveit-resources-panda-moveit-config

ros2 launch moveit_resources_panda_moveit_config demo.launch.py
Example URDF Display Launch File Provided

This launch file was given to validate the URDF before MoveIt:

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    urdf = os.path.join(
        get_package_share_directory('my_rover_description'),
        'urdf',
        'robot.urdf'
    )

    return LaunchDescription([

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': open(urdf).read()
            }]
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui'
        ),

        Node(
            package='rviz2',
            executable='rviz2'
        )
    ])
Example MoveIt Python Usage Provided
MoveItPy example
from moveit.planning import MoveItPy

panda = MoveItPy(node_name="moveit_py")
arm = panda.get_planning_component("arm")

arm.set_start_state_to_current_state()

arm.set_goal_state(
    pose_stamped=target_pose,
    pose_link="tool0"
)

plan = arm.plan()

if plan:
    panda.execute(plan)
5. Open Problems and Pending Tasks
Immediate Next Tasks

The user still needs to:

Confirm ROS 2 installation
Install MoveIt 2
Create workspace
Verify MoveIt launches
Test Panda example
Add rover URDF package
Verify URDF in RViz
Generate MoveIt config package
Test arm planning
Important Missing Information

The user has NOT yet specified:

Exact Ubuntu version
Exact ROS distro
Whether Gazebo/Ignition is used
Real hardware vs simulation
Arm DOF count
Differential/Ackermann/omni rover base
Whether URDF uses xacro
ros2_control status
Existing controller setup
Hardware interface type

These are still uncertain.

Potential Future Topics

Likely future assistance areas:

MoveIt Setup Assistant troubleshooting
SRDF configuration
ros2_control integration
Gazebo simulation
Fake controllers
Hardware controllers
IK tuning
Collision matrix tuning
OMPL tuning
MoveIt Servo
Cartesian planning
Whole-body planning
Nav2 integration
6. Important Conversation Insights
User Communication Preference

The user prefers:

Direct technical guidance
Step-by-step procedures
Practical commands and examples
Structured explanations

The assistant responded with:

Ordered steps
Explicit commands
Architecture guidance
Warnings about common pitfalls
Important Priorities

The assistant emphasized:

Incremental validation
Avoiding premature complexity
Verifying URDF before MoveIt
Starting fixed-base first
Things to Avoid Repeating

Avoid repeatedly suggesting:

Whole-body planning initially
Planar virtual joints initially
Complex controller setups before RViz validation

The conversation already strongly established:

“Get arm-only planning working first.”

7. Technical Details
Recommended MoveIt Setup Flow
Virtual Joint
world -> base_link
type: fixed
Planning Group
Group name: arm
base: arm_base_link
tip: tool0
Suggested Package Layout
my_rover_description/
├── urdf/
├── meshes/
├── launch/
├── package.xml
└── CMakeLists.txt
Suggested Validation Sequence

Strongly recommended order:

URDF visible in RViz
TF tree correct
Arm-only MoveIt planning
Fake controllers
Real controllers
Gazebo execution
Mobile-base integration
Important Commands
Validate URDF
check_urdf my_robot.urdf
Build workspace
colcon build --symlink-install
Source workspace
source install/setup.bash
Launch MoveIt Setup Assistant
ros2 launch moveit_setup_assistant setup_assistant.launch.py
Launch generated MoveIt config
ros2 launch my_rover_moveit_config demo.launch.py
Common Failure Causes Mentioned
MoveIt failures commonly caused by:
Missing collision geometry
Bad TF chain
Missing joint limits
Incorrect end-effector link
Continuous joints without limits
8. Exact Artifacts to Preserve
Key Installation Commands
sudo apt update
sudo apt install ros-humble-moveit
sudo apt install \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-joint-trajectory-controller
sudo apt install \
  ros-humble-xacro \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-tf2-tools \
  ros-humble-rviz2
Workspace Setup
mkdir -p ~/ws_moveit/src
cd ~/ws_moveit
colcon build
source install/setup.bash
Launch Setup Assistant
ros2 launch moveit_setup_assistant setup_assistant.launch.py
Panda Test
sudo apt install ros-humble-moveit-resources-panda-moveit-config

ros2 launch moveit_resources_panda_moveit_config demo.launch.py
URDF RViz Launch File

Preserve the full Python launch file from section 4 above.

MoveItPy Example
from moveit.planning import MoveItPy

panda = MoveItPy(node_name="moveit_py")
arm = panda.get_planning_component("arm")

arm.set_start_state_to_current_state()

arm.set_goal_state(
    pose_stamped=target_pose,
    pose_link="tool0"
)

plan = arm.plan()

if plan:
    panda.execute(plan)
Recommended Next Prompt

A good next prompt for the next AI instance would be:

“I’ve installed MoveIt 2 on ROS 2 Humble. Here is my rover URDF/Xacro structure and current package layout. Help me generate a proper MoveIt configuration package step-by-step and debug any issues.”



