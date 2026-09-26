import numpy as np
from scipy.optimize import minimize
from urdf_fk import URDFForwardKinematics

class URDFInverseKinematics(URDFForwardKinematics):
    def __init__(self, urdf_file):
        super().__init__(urdf_file)

    def inverse_kinematics(self, target_pos, target_rpy=None, initial_guess=None, target_link=None):
        """
        Calculate Inverse Kinematics using numerical optimization (scipy).
        
        Args:
            target_pos: np.array [x, y, z] target position
            target_rpy: np.array [roll, pitch, yaw] target orientation (optional)
            initial_guess: dict {joint_name: value} (optional)
            target_link: name of the link to solve for (optional)
            
        Returns:
            result_joints: dict {joint_name: value}
            success: bool
        """
        target_pos = np.array(target_pos)
        
        # 1. Determine active chain
        # Run FK once with dummy values to get the chain list
        _, _, chain = self.forward_kinematics({}, target_link)
        
        # Filter for active joints
        active_joints = [j for j in chain if self.joints[j]['type'] in ['revolute', 'continuous', 'prismatic']]
        
        if not active_joints:
            return {}, True # No joints to move
            
        # 2. Setup bounds and initial guess
        bounds = []
        x0 = []
        for j in active_joints:
            limits = self.joints[j].get('limits', (-np.pi, np.pi))
            bounds.append(limits)
            if initial_guess and j in initial_guess:
                x0.append(initial_guess[j])
            else:
                # Default guess: center of range or 0
                mid = (limits[0] + limits[1]) / 2.0
                x0.append(mid if np.isfinite(mid) else 0.0)
        
        # 3. Objective Function
        def objective(x):
            # Map optimization vector x back to joint dict
            current_joints = {name: val for name, val in zip(active_joints, x)}
            
            # Forward Kinematics
            T, _, _ = self.forward_kinematics(current_joints, target_link)
            current_pos = T[:3, 3]
            
            # Position Error (Squared Euclidean Distance)
            pos_error = np.sum((current_pos - target_pos)**2)
            
            # Orientation Error (if provided)
            rot_error = 0.0
            if target_rpy is not None:
                R_target = self._rpy_to_matrix(target_rpy)
                R_current = T[:3, :3]
                # Frobenius norm of difference: ||R_target - R_current||_F
                rot_error = np.sum((R_target - R_current)**2)
            
            return pos_error + rot_error
            
        # 4. Run Optimization
        # SLSQP is good for bound-constrained problems
        res = minimize(objective, x0, bounds=bounds, method='SLSQP', tol=1e-6)
        
        # 5. Format Result
        result_joints = {name: val for name, val in zip(active_joints, res.x)}
        
        return result_joints, res.success

def main():
    urdf_path = r"d:\ROS\urdf\genkiarm.urdf"
    ik_solver = URDFInverseKinematics(urdf_path)
    
    print("--- Inverse Kinematics Test (Separate File) ---")
    
    # Target: Let's pick a known reachable point (e.g., from Rotation=90deg case)
    # Position (XYZ): [ 0.0005 -0.0002  0.428 ]
    target_pos = np.array([5.197e-04, -2.552e-04, 4.279e-01])
    
    print(f"Target Position: {target_pos}")
    
    # Initial guess (all zeros)
    initial_guess = {k: 0.0 for k in ik_solver.joints.keys()}
    
    result_joints, success = ik_solver.inverse_kinematics(target_pos, initial_guess=initial_guess)
    
    print(f"IK Success: {success}")
    print("Resulting Joints:")
    for k, v in result_joints.items():
        print(f"  {k}: {v:.4f} rad ({np.degrees(v):.2f} deg)")
        
    # Verify result
    xyz, _ = ik_solver.get_end_effector_pose(result_joints)
    print(f"Verified Position: {xyz}")
    print(f"Error: {np.linalg.norm(xyz - target_pos)}")

if __name__ == "__main__":
    main()
