import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
import os
from ament_index_python.packages import get_package_share_directory
import numpy as np
from arm_pkg.urdf_ik import URDFInverseKinematics
from arm_msg.msg import ArmJointAngles
import time
import threading

class ArmCatchBoxNode2(Node):
    def __init__(self):
        super().__init__('arm_catch_box_node2')
        self.get_logger().info('Arm Catch Box Node 2 has been started.')

        # Publisher for joint angles
        self.publisher_ = self.create_publisher(ArmJointAngles, 'cmd_angles', 10)

        # Find URDF file
        package_share_directory = get_package_share_directory('arm_pkg')
        urdf_path = os.path.join(package_share_directory, 'urdf', 'genkiarm.urdf')
        
        if not os.path.exists(urdf_path):
             self.get_logger().error(f'URDF file not found at: {urdf_path}')
        else:
             self.get_logger().info(f'Loaded URDF from: {urdf_path}')

        # Initialize IK Solver
        try:
            self.ik_solver = URDFInverseKinematics(urdf_path)
            self.get_logger().info('IK Solver initialized successfully.')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize IK Solver: {str(e)}')
            self.ik_solver = None

        # Subscribe to box_world_pos
        self.subscription = self.create_subscription(
            Point,
            'box_world_pos',
            self.listener_callback,
            10)
        self.subscription
        
        # Subscribe to arm_joint_angles to get current state
        self.joint_subscription = self.create_subscription(
            ArmJointAngles,
            'arm_joint_angles',
            self.joint_callback,
            10)
        self.current_joints = [0.0] * 6

        # State flag to ignore new messages while executing a sequence
        self.is_busy = False
        
        # Gripper constants (Rotation6 limits: 0 to 1.57)
        self.GRIPPER_OPEN = 0.0  # Assumed Open
        self.GRIPPER_CLOSE = -90.0  # Assumed Closed

        # Joint Mapping
        self.joint_map = {
            'Rotation': 0,   # Base
            'Rotation2': 1,  # Shoulder
            'Rotation3': 2,  # Elbow
            'Rotation4': 3,  # Wrist 1
            'Rotation5': 4,  # Wrist 2
            'Rotation6': 5   # Gripper
        }

    def joint_callback(self, msg):
        # Update current joint angles
        if len(msg.angles) == 6:
            self.current_joints = list(msg.angles)

    def listener_callback(self, msg):
        if self.ik_solver is None:
            return

        if self.is_busy:
            self.get_logger().info('Node is busy executing sequence. Ignoring new coordinate.')
            return

        self.get_logger().info(f'Received Target Position: x={msg.x}, y={msg.y}, z={msg.z}')
        
        # Mark as busy
        self.is_busy = True
        
        # Start execution in a separate thread to not block the callback
        threading.Thread(target=self.execute_sequence, args=(msg,)).start()

    def execute_sequence(self, msg):
        try:
            target_pos = np.array([msg.x-0.02, msg.y+0.01, msg.z+0.05])
            lift_pos = np.array([msg.x, msg.y, msg.z + 0.3])
            
            self.get_logger().info('Starting Sequence...')

            # Step 1: Open Gripper at Current Position
            self.get_logger().info('Step 1: Opening Gripper')
            # Use current joints but set gripper to OPEN
            joint_values_open = list(self.current_joints)
            joint_values_open[5] = self.GRIPPER_OPEN
            self.publish_angles(joint_values_open)
            time.sleep(2) # Wait for gripper to open

            # Step 2: Move to Target (with OPEN gripper)
            self.get_logger().info('Step 2: Moving to Target')
            joint_values_target = self.solve_ik(target_pos)
            
            if joint_values_target:
                # Ensure gripper stays OPEN
                joint_values_target[5] = self.GRIPPER_OPEN
                self.publish_angles(joint_values_target)
                time.sleep(4) # Wait for movement
            else:
                self.get_logger().error('IK failed for target position. Aborting sequence.')
                self.is_busy = False
                return

            # Step 3: Close Gripper
            self.get_logger().info('Step 3: Closing Gripper')
            # Keep same arm position (from Step 2), just change gripper
            joint_values_target[5] = self.GRIPPER_CLOSE
            self.publish_angles(joint_values_target)
            time.sleep(2) # Wait for gripper to close

            # Step 4: Lift Arm (z + 0.2m)
            self.get_logger().info('Step 4: Lifting Arm (z + 0.2m)')
            joint_values_lift = self.solve_ik(lift_pos)
            
            if joint_values_lift:
                # Keep gripper CLOSED
                joint_values_lift[5] = self.GRIPPER_CLOSE
                self.publish_angles(joint_values_lift)
                time.sleep(4) # Wait for movement
            else:
                self.get_logger().error('IK failed for lift position.')
            
            self.get_logger().info('Sequence Completed.')

        except Exception as e:
            self.get_logger().error(f'Error during sequence execution: {str(e)}')
        finally:
            # self.is_busy = False
            self.get_logger().info('Ready for new commands.')

    def solve_ik(self, target_pos):
        initial_guess = {k: 0.0 for k in self.ik_solver.joints.keys()}
        result_joints, success = self.ik_solver.inverse_kinematics(target_pos, initial_guess=initial_guess)
        
        if success:
            joint_values = [0.0] * 6
            for k, v in result_joints.items():
                if k in self.joint_map:
                    idx = self.joint_map[k]
                    joint_values[idx] = float(np.degrees(v))
            return joint_values
        else:
            return None

    def publish_angles(self, joint_values):
        msg_angles = ArmJointAngles()
        msg_angles.angles = joint_values
        self.publisher_.publish(msg_angles)
        self.get_logger().info(f'Published: {joint_values}')

def main(args=None):
    rclpy.init(args=args)
    node = ArmCatchBoxNode2()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
