import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QFormLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import QTimer
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

class TurtleAdvceGui(QWidget):
    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self.pub = self.node.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.sub = self.node.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        
        self.setWindowTitle('小乌龟控制器')
        layout = QFormLayout(self)
        
        self.linear_edit = QLineEdit('0.0')
        self.angular_edit = QLineEdit('0.0')
        self.pos_x_label = QLabel('0.0')
        self.pos_y_label = QLabel('0.0')
        self.linear_vel_label = QLabel('0.0')
        self.angular_vel_label = QLabel('0.0')
        self.theta_label = QLabel('0.0')
        self.send_btn = QPushButton('发送')
        
        layout.addRow('线速度', self.linear_edit)
        layout.addRow('角速度 (度)', self.angular_edit)
        layout.addRow('当前X坐标', self.pos_x_label)
        layout.addRow('当前Y坐标', self.pos_y_label)
        layout.addRow('当前线速度', self.linear_vel_label)
        layout.addRow('当前角速度', self.angular_vel_label)
        layout.addRow('当前角度', self.theta_label)
        layout.addRow(self.send_btn)
        
        self.send_btn.clicked.connect(self.on_send)
        
        # Timer to process ROS events
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.spin_ros)
        self.timer.start(10)  # 10ms

    def spin_ros(self):
        # We need to manually spin the node to process callbacks because we are in PyQt event loop
        # However, rclpy.spin is blocking. We should use spin_once with timeout 0
        rclpy.spin_once(self.node, timeout_sec=0)

    def pose_callback(self, msg):
        self.pos_x_label.setText(f'{msg.x:.6f}')
        self.pos_y_label.setText(f'{msg.y:.6f}')
        self.linear_vel_label.setText(f'{msg.linear_velocity:.6f}')
        self.angular_vel_label.setText(f'{msg.angular_velocity:.6f}')
        self.theta_label.setText(f'{msg.theta:.6f}')

    def on_send(self):
        try:
            linear = float(self.linear_edit.text())
        except ValueError:
            linear = 0.0
        try:
            angular_deg = float(self.angular_edit.text())
        except ValueError:
            angular_deg = 0.0
        
        # 将角度转换为弧度
        angular_rad = math.radians(angular_deg)
        
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular_rad
        self.pub.publish(msg)
        self.node.get_logger().info(f'Publishing: linear.x={linear}, angular.z={angular_rad} (deg={angular_deg})')

def main(args=None):
    rclpy.init(args=args)
    node = Node('turtle_advce_ctrl_node')
    
    app = QApplication(sys.argv)
    w = TurtleAdvceGui(node)
    w.show()
    
    exit_code = app.exec_()
    
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
