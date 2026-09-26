import xml.etree.ElementTree as ET
import numpy as np
import os

class URDFForwardKinematics:
    def __init__(self, urdf_file):
        self.urdf_file = urdf_file
        self.joints = {}
        self.links = {}
        self.root_link = None
        self._parse_urdf()

    def _parse_urdf(self):
        if not os.path.exists(self.urdf_file):
            raise FileNotFoundError(f"URDF file not found: {self.urdf_file}")

        tree = ET.parse(self.urdf_file)
        robot = tree.getroot()
        
        # Parse joints
        for joint in robot.findall('joint'):
            name = joint.get('name')
            joint_type = joint.get('type')
            parent = joint.find('parent').get('link')
            child = joint.find('child').get('link')
            
            origin = joint.find('origin')
            xyz = [0.0, 0.0, 0.0]
            rpy = [0.0, 0.0, 0.0]
            if origin is not None:
                if origin.get('xyz'):
                    xyz = [float(x) for x in origin.get('xyz').split()]
                if origin.get('rpy'):
                    rpy = [float(x) for x in origin.get('rpy').split()]
            
            axis = [1.0, 0.0, 0.0] # Default axis
            axis_elem = joint.find('axis')
            if axis_elem is not None and axis_elem.get('xyz'):
                axis = [float(x) for x in axis_elem.get('xyz').split()]
            
            # Parse limits
            lower = -np.pi
            upper = np.pi
            limit = joint.find('limit')
            if limit is not None:
                if limit.get('lower'):
                    lower = float(limit.get('lower'))
                if limit.get('upper'):
                    upper = float(limit.get('upper'))
            
            self.joints[name] = {
                'type': joint_type,
                'parent': parent,
                'child': child,
                'xyz': np.array(xyz),
                'rpy': np.array(rpy),
                'axis': np.array(axis),
                'limits': (lower, upper)
            }
        
        # Identify links and root
        all_links = set()
        child_links = set()
        for j in self.joints.values():
            all_links.add(j['parent'])
            all_links.add(j['child'])
            child_links.add(j['child'])
        
        # Root link is the one that is never a child
        root_candidates = all_links - child_links
        if root_candidates:
            self.root_link = list(root_candidates)[0]
        else:
            self.root_link = "Base"

    def _rpy_to_matrix(self, rpy):
        """
        Convert Roll-Pitch-Yaw to Rotation Matrix.
        URDF rpy is fixed axis XYZ (Roll around X, Pitch around Y, Yaw around Z)
        Equivalent to: R = Rz(y) * Ry(p) * Rx(r)
        """
        r, p, y = rpy
        
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(r), -np.sin(r)],
            [0, np.sin(r), np.cos(r)]
        ])
        
        Ry = np.array([
            [np.cos(p), 0, np.sin(p)],
            [0, 1, 0],
            [-np.sin(p), 0, np.cos(p)]
        ])
        
        Rz = np.array([
            [np.cos(y), -np.sin(y), 0],
            [np.sin(y), np.cos(y), 0],
            [0, 0, 1]
        ])
        
        return Rz @ Ry @ Rx

    def _axis_angle_rotation(self, axis, angle):
        """
        Rodrigues' rotation formula or simple axis rotation matrix
        """
        # Normalize axis
        axis = axis / np.linalg.norm(axis)
        ux, uy, uz = axis
        c = np.cos(angle)
        s = np.sin(angle)
        
        R = np.array([
            [c + ux**2 * (1-c),    ux*uy*(1-c) - uz*s, ux*uz*(1-c) + uy*s],
            [uy*ux*(1-c) + uz*s, c + uy**2 * (1-c),    uy*uz*(1-c) - ux*s],
            [uz*ux*(1-c) - uy*s, uz*uy*(1-c) + ux*s, c + uz**2 * (1-c)]
        ])
        return R

    def _rotation_matrix_to_rpy(self, R):
        """
        Convert Rotation Matrix to Roll-Pitch-Yaw (URDF fixed axis convention: R = Rz(y)*Ry(p)*Rx(r))
        """
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6
        
        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])  # Roll
            y = np.arctan2(-R[2, 0], sy)      # Pitch
            z = np.arctan2(R[1, 0], R[0, 0])  # Yaw
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0
            
        return np.array([x, y, z])

    def get_transform(self, joint_name, joint_value):
        if joint_name not in self.joints:
            raise ValueError(f"Joint {joint_name} not found")
            
        joint = self.joints[joint_name]
        
        # 1. Fixed transform from parent to joint frame (origin)
        T_origin = np.eye(4)
        T_origin[:3, 3] = joint['xyz']
        T_origin[:3, :3] = self._rpy_to_matrix(joint['rpy'])
        
        # 2. Joint variable transform
        T_joint = np.eye(4)
        if joint['type'] == 'revolute' or joint['type'] == 'continuous':
            R_joint = self._axis_angle_rotation(joint['axis'], joint_value)
            T_joint[:3, :3] = R_joint
        elif joint['type'] == 'prismatic':
            T_joint[:3, 3] = joint['axis'] * joint_value
        
        # Total transform
        return T_origin @ T_joint

    def forward_kinematics(self, joint_values, target_link=None):
        """
        Calculate FK.
        joint_values: dict {joint_name: value}
        target_link: name of the link to calculate pose for (default: last link found)
        """
        # 1. Map links to their parent joints
        link_parent_joint = {}
        for name, data in self.joints.items():
            link_parent_joint[data['child']] = name
            
        # If no target link, try to find a leaf link (end effector)
        if target_link is None:
            all_parents = set(j['parent'] for j in self.joints.values())
            all_children = set(j['child'] for j in self.joints.values())
            leaves = all_children - all_parents
            if leaves:
                target_link = list(leaves)[0]
            else:
                target_link = list(all_children)[-1]
        
        # Trace back from target to root
        chain = []
        current_link = target_link
        while current_link != self.root_link:
            if current_link not in link_parent_joint:
                break # Reached root or disconnected
            joint_name = link_parent_joint[current_link]
            chain.append(joint_name)
            current_link = self.joints[joint_name]['parent']
        
        chain.reverse() # Root to target
        
        # Compute transform
        T_total = np.eye(4)
        transforms = {}
        
        for joint_name in chain:
            val = joint_values.get(joint_name, 0.0)
            T = self.get_transform(joint_name, val)
            T_total = T_total @ T
            transforms[joint_name] = T_total.copy()
            
        return T_total, transforms, chain

    def get_end_effector_pose(self, joint_values, target_link=None):
        """
        Computes the end effector position and orientation (RPY) for the given joint values.
        """
        T_final, _, _ = self.forward_kinematics(joint_values, target_link)
        xyz = T_final[:3, 3]
        rpy = self._rotation_matrix_to_rpy(T_final[:3, :3])
        return xyz, rpy

def main():
    urdf_path = r"d:\ROS\urdf\genkiarm.urdf"
    fk_solver = URDFForwardKinematics(urdf_path)
    
    print(f"Root Link: {fk_solver.root_link}")
    print(f"Joints found: {list(fk_solver.joints.keys())}")
    
    # Test with 0 angles
    joint_values = {
        'Rotation': 0.0,
        'Rotation2': 0.0,
        'Rotation3': 0.0,
        'Rotation4': 0.0,
        'Rotation5': 0.0,
        'Rotation6': 0.0
    }
    
    xyz, rpy = fk_solver.get_end_effector_pose(joint_values)
    print("\n--- Joint Values: All Zeros ---")
    print(f"Position (XYZ): {xyz}")
    print(f"Orientation (RPY): {rpy} (radians)")
    print(f"Orientation (RPY): {np.degrees(rpy)} (degrees)")
    
    # Test with some angles (e.g., 90 degrees on first joint)
    joint_values['Rotation'] = np.pi/2
    xyz, rpy = fk_solver.get_end_effector_pose(joint_values)
    print("\n--- Joint Values: Rotation = 90 deg ---")
    print(f"Position (XYZ): {xyz}")
    print(f"Orientation (RPY): {rpy} (radians)")
    print(f"Orientation (RPY): {np.degrees(rpy)} (degrees)")

if __name__ == "__main__":
    main()
