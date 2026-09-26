import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QFormLayout, QLineEdit, QPushButton
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class TurtleGui(QWidget):
    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self.pub = self.node.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.setWindowTitle('小乌龟控制器')
        layout = QFormLayout(self)
        self.linear_edit = QLineEdit('0.0')
        self.angular_edit = QLineEdit('0.0')
        self.send_btn = QPushButton('发送')
        layout.addRow('线速度', self.linear_edit)
        layout.addRow('角速度 (度)', self.angular_edit)
        layout.addRow(self.send_btn)
        self.send_btn.clicked.connect(self.on_send)

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
    node = Node('turtle_gui_ctrl_node')
    app = QApplication(sys.argv)
    w = TurtleGui(node)
    w.show()
    exit_code = app.exec_()
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()

