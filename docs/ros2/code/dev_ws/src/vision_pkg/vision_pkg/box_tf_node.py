import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Float32MultiArray
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

class BoxTFNode(Node):
    def __init__(self):
        super().__init__('box_tf_node')
        self.get_logger().info('Box TF Node has been started with URDF-based Coordinate System.')

        # ==========================================
        # Configuration Section (Parameters)
        # ==========================================
        # Camera Position in Arm Coordinate System (Unit: meters)
        # 摄像头在机械臂基座坐标系(Base Link)中的位置
        # Base Link Definition based on genkiarm.urdf:
        # Origin: Robot Base
        # X Axis: Forward (Robot Front)
        # Y Axis: Left
        # Z Axis: Up (Vertical)
        self.declare_parameter('camera_x', 0.18)
        self.declare_parameter('camera_y', 0.02)
        self.declare_parameter('camera_z', 0.5)
        
        # Rotation of Camera Frame (Unit: degrees)
        # 摄像头绕 Base Z轴 的旋转角度 (Yaw)
        # 0度定义: 摄像头图像上方(Top)指向 Base +X (Forward)
        self.declare_parameter('camera_rotation_degree', 180)
        
        # Pixel to Physical Scale Ratio (Unit: meters/pixel)
        self.declare_parameter('scale_ratio', 0.001) 

        # Physical Width of the Box (Unit: meters)
        self.declare_parameter('box_physical_width', 0.03)
        
        # Image Resolution
        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)
        # ==========================================

        self.subscription = self.create_subscription(
            Float32MultiArray,
            'box_info',
            self.listener_callback,
            10)
        
        self.publisher_ = self.create_publisher(Point, 'box_world_pos', 10)
        
        # Initialize Matplotlib Visualization
        # plt.ion() # Interactive mode
        # self.fig, self.ax = plt.subplots(figsize=(8, 8))
        # self.ax.set_title("Arm Coordinate System (Standard View)\nBase Frame: X=Forward, Y=Left")
        
        # # Align Plot Axes with Robot Axes directly
        # # Plot X Axis = Robot X (Forward)
        # # Plot Y Axis = Robot Y (Left)
        # self.ax.set_xlabel("Base X (Forward) [m]")
        # self.ax.set_ylabel("Base Y (Left) [m]")
        # self.ax.grid(True)
        # self.ax.axis('equal')
        
        # # Initial Limits (Adjustable by user via Pan/Zoom)
        # self.ax.set_xlim(-0.1, 0.6) # Focus on Forward direction
        # self.ax.set_ylim(-0.5, 0.5)

        # self.scat_cam, = self.ax.plot([], [], 'bo', label='Camera Pos', markersize=10)
        # self.scat_obj, = self.ax.plot([], [], 'y*', label='Object', markersize=15)
        # self.text_cam = self.ax.text(0, 0, '', fontsize=9, color='blue')
        # self.text_obj = self.ax.text(0, 0, '', fontsize=9, color='olive')
        
        # # Draw Arm Base
        # self.ax.plot(0, 0, 'ks', markersize=12, label='Arm Base (0,0)')
        
        # # Draw Axes for Reference (Aligned with Plot Axes)
        # # Base X (Forward) -> Plot X (Right)
        # self.ax.arrow(0, 0, 0.1, 0, head_width=0.02, color='red', label='Base X (Fwd)')
        
        # # Base Y (Left) -> Plot Y (Up)
        # self.ax.arrow(0, 0, 0, 0.1, head_width=0.02, color='green', label='Base Y (Left)')
        
        # # Camera Axes Quivers (Initialized with dummy data to ensure rendering)
        # # Initialize with visible dummy arrows at origin
        # self.quiver_cam_x = self.ax.quiver([0], [0], [0.1], [0], color='cyan', scale=1, scale_units='xy', angles='xy', width=0.015, headwidth=4, headlength=5, zorder=5)
        # self.quiver_cam_y = self.ax.quiver([0], [0], [0], [0.1], color='magenta', scale=1, scale_units='xy', angles='xy', width=0.015, headwidth=4, headlength=5, zorder=5)

        # # Custom Legend
        # custom_lines = [
        #     Line2D([0], [0], color='blue', marker='o', linestyle='None', markersize=10),
        #     Line2D([0], [0], color='gold', marker='*', linestyle='None', markersize=15),
        #     Line2D([0], [0], color='black', marker='s', linestyle='None', markersize=12),
        #     Line2D([0], [0], color='red', lw=2),
        #     Line2D([0], [0], color='green', lw=2),
        #     Line2D([0], [0], color='cyan', lw=2),
        #     Line2D([0], [0], color='magenta', lw=2)
        # ]
        # self.ax.legend(custom_lines, 
        #                ['Camera Pos', 'Object', 'Arm Base', 'Base X (Fwd)', 'Base Y (Left)', 'Cam X (Right)', 'Cam Y (Down)'], 
        #                loc='upper left')

    def update_visualization(self, arm_x, arm_y, cam_x, cam_y, cam_axis_x, cam_axis_y):
        pass
        # try:
        #     # Map Arm Coordinates to Plot Coordinates DIRECTLY
        #     # Plot X = Arm X
        #     # Plot Y = Arm Y
            
        #     plot_cam_x = cam_x
        #     plot_cam_y = cam_y
            
        #     plot_obj_x = arm_x
        #     plot_obj_y = arm_y
            
        #     # Update Points
        #     self.scat_cam.set_data([plot_cam_x], [plot_cam_y])
        #     self.scat_obj.set_data([plot_obj_x], [plot_obj_y])
            
        #     self.text_cam.set_position((plot_cam_x + 0.02, plot_cam_y))
        #     self.text_cam.set_text(f"Cam\n({cam_x:.2f}, {cam_y:.2f})")
            
        #     self.text_obj.set_position((plot_obj_x + 0.02, plot_obj_y))
        #     self.text_obj.set_text(f"Obj\n({arm_x:.2f}, {arm_y:.2f})")
            
        #     # Update Camera Axes
        #     # Vector Mapping: Direct
            
        #     # Cam X Axis
        #     u_cam_x = cam_axis_x[0] * 0.1 # Scale length 0.1m
        #     v_cam_x = cam_axis_x[1] * 0.1
        #     self.quiver_cam_x.set_offsets([[plot_cam_x, plot_cam_y]])
        #     self.quiver_cam_x.set_UVC([u_cam_x], [v_cam_x])
            
        #     # Cam Y Axis
        #     u_cam_y = cam_axis_y[0] * 0.1 # Scale length 0.1m
        #     v_cam_y = cam_axis_y[1] * 0.1
        #     self.quiver_cam_y.set_offsets([[plot_cam_x, plot_cam_y]])
        #     self.quiver_cam_y.set_UVC([u_cam_y], [v_cam_y])

        #     # Refresh
        #     self.fig.canvas.draw_idle()
        #     self.fig.canvas.flush_events()
            
        # except Exception as e:
        #     pass # Ignore drawing errors during shutdown

    def listener_callback(self, msg):
        try:
            if len(msg.data) < 4:
                return

            # Extract Data
            u = msg.data[0] # cx
            v = msg.data[1] # cy
            w_px = msg.data[2] # width
            h_px = msg.data[3] # height

            # Get Parameters
            cam_x = self.get_parameter('camera_x').value
            cam_y = self.get_parameter('camera_y').value
            cam_z = self.get_parameter('camera_z').value
            rotation_deg = self.get_parameter('camera_rotation_degree').value
            default_scale = self.get_parameter('scale_ratio').value
            physical_width = self.get_parameter('box_physical_width').value
            width = self.get_parameter('image_width').value
            height = self.get_parameter('image_height').value

            # Calculate Scale dynamically
            scale = default_scale
            if w_px > 0 and physical_width > 0:
                scale = physical_width / w_px

            # Image Center
            cx = width / 2.0
            cy = height / 2.0

            # =========================================================
            # Coordinate Transformation Logic (URDF Based)
            # =========================================================
            # 1. Base Frame (URDF 'Base'):
            #    X: Forward, Y: Left, Z: Up
            #
            # 2. Camera Rotation (Yaw around Base Z):
            #    We define an intermediate 'Rotated Base' frame by rotating 
            #    Base frame by 'rotation_deg' around Z.
            #
            # 3. Camera Optical Frame (Standard CV):
            #    X_cam: Right (Image Right)
            #    Y_cam: Down (Image Down)
            #    Z_cam: Forward (Optical Axis)
            #
            # 4. Mapping Camera Optical Frame to Rotated Base Frame:
            #    (Assumption: Camera is looking DOWN)
            #    Cam Z (Forward) -> Rotated Base -Z (Down)
            #    Cam X (Right)   -> Rotated Base -Y (Right)
            #    Cam Y (Down)    -> Rotated Base -X (Back)
            
            theta = math.radians(rotation_deg)
            c = math.cos(theta)
            s = math.sin(theta)

            # Basis Vectors of Rotated Base Frame expressed in Original Base Frame
            # X_prime = [c, s, 0]
            # Y_prime = [-s, c, 0]
            # Z_prime = [0, 0, 1]

            # Camera Basis Vectors expressed in Original Base Frame
            # Cam_X = -Y_prime
            # Cam_Y = -X_prime
            
            cam_axis_x_in_base = np.array([s, -c, 0])   # -(-s, c, 0)
            cam_axis_y_in_base = np.array([-c, -s, 0])  # -(c, s, 0)
            
            # Displacement in Camera Plane (meters)
            dx_cam = (u - cx) * scale
            # Invert Y axis: In image coordinates, Y increases downwards.
            # In standard camera optical frame (Cartesian), we often want Y to increase downwards (standard CV) 
            # OR we need to account for pixel-to-meter conversion direction.
            # User requested inversion: "y axis needs to be inverted because camera coordinate system is not Cartesian"
            # This likely refers to pixel v coordinate increasing downwards vs Cartesian Y increasing upwards.
            dy_cam = -(v - cy) * scale 
            
            # Vector from Camera Origin to Object (in Base Frame)
            # V = dx * Cam_X + dy * Cam_Y
            vec_to_obj = dx_cam * cam_axis_x_in_base + dy_cam * cam_axis_y_in_base
            
            # Camera Origin in Base Frame
            p_cam_origin = np.array([cam_x, cam_y, cam_z])
            
            # Object Position in Base Frame
            p_obj_base = p_cam_origin + vec_to_obj
            
            # Final Coordinates
            arm_x = float(p_obj_base[0])
            arm_y = float(p_obj_base[1])
            arm_z = 0.0 # Hardcoded Z height as requested (10cm)
            
            # Publish
            world_point = Point()
            world_point.x = arm_x
            world_point.y = arm_y
            world_point.z = arm_z
            
            self.publisher_.publish(world_point)
            
            # Visualization
            self.update_visualization(arm_x, arm_y, cam_x, cam_y, cam_axis_x_in_base, cam_axis_y_in_base)
            
        except Exception as e:
            self.get_logger().error(f'Error transforming coordinates: {str(e)}')

    def destroy_node(self):
        # plt.close(self.fig)
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = BoxTFNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
