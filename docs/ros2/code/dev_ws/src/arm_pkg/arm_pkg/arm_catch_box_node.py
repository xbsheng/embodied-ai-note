import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
import os
from ament_index_python.packages import get_package_share_directory
import numpy as np
from arm_pkg.urdf_ik import URDFInverseKinematics
from arm_msg.msg import ArmJointAngles

class ArmCatchBoxNode(Node):
    def __init__(self):
        super().__init__('arm_catch_box_node')
        self.get_logger().info('Arm Catch Box Node has been started.')

        # Publisher for joint angles
        self.publisher_ = self.create_publisher(ArmJointAngles, 'cmd_angles', 10)

        # Find URDF file
        package_share_directory = get_package_share_directory('arm_pkg')
        urdf_path = os.path.join(package_share_directory, 'urdf', 'genkiarm.urdf')
        
        if not os.path.exists(urdf_path):
             self.get_logger().error(f'URDF file not found at: {urdf_path}')
             # Fallback for development if not installed yet (optional)
             # urdf_path = "/home/itheima/dev_ws/src/arm_pkg/urdf/genkiarm.urdf"
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

    def listener_callback(self, msg):
        if self.ik_solver is None:
            return

        try:
            # User requested to raise Z by 0.2m before IK
            target_pos = np.array([msg.x, msg.y, msg.z + 0.2])
            self.get_logger().info(f'Received Target Position (with +0.2m offset): {target_pos}')

            # Perform Inverse Kinematics
            # Initial guess can be previous state or zeros
            initial_guess = {k: 0.0 for k in self.ik_solver.joints.keys()}
            
            # Note: You might want to define target orientation (RPY) as well
            # For catching a box, maybe the gripper should be pointing down?
            # target_rpy = [0, np.pi/2, 0] # Example: Pitch 90 deg down? 
            # For now, let's try position only or default behavior of urdf_ik
            
            result_joints, success = self.ik_solver.inverse_kinematics(target_pos, initial_guess=initial_guess)

            if success:
                self.get_logger().info('IK Calculation Successful!')
                
                # Publish Joint Angles
                msg_angles = ArmJointAngles()
                # Initialize with 0.0 for 6 joints
                joint_values = [0.0] * 6
                
                self.get_logger().info('Resulting Joint Angles:')
                
                # Mapping based on genkiarm.urdf joint names to Servo IDs (1-6) -> Indices (0-5)
                joint_map = {
                    'Rotation': 0,   # Base
                    'Rotation2': 1,  # Shoulder
                    'Rotation3': 2,  # Elbow
                    'Rotation4': 3,  # Wrist 1
                    'Rotation5': 4,  # Wrist 2
                    'Rotation6': 5   # Gripper/EndEffector
                }
                
                for k, v in result_joints.items():
                    degrees = np.degrees(v)
                    self.get_logger().info(f'  {k}: {v:.4f} rad ({degrees:.2f} deg)')
                    
                    if k in joint_map:
                        idx = joint_map[k]
                        joint_values[idx] = float(degrees)
                    else:
                        self.get_logger().warn(f'Could not map joint {k} to index')

                msg_angles.angles = joint_values
                self.publisher_.publish(msg_angles)
                self.get_logger().info(f'Published Joint Angles: {joint_values}')

            else:
                self.get_logger().warn('IK Calculation Failed to Converge.')

        except Exception as e:
            self.get_logger().error(f'Error during IK calculation: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = ArmCatchBoxNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
