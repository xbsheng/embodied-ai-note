import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class TurtleCtrlNode(Node):
    def __init__(self):
        super().__init__('turtle_ctrl_node')
        # 创建发布者，消息类型Twist，话题名/turtle1/cmd_vel，队列长度10
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        # 创建定时器，0.5秒执行一次
        self.timer = self.create_timer(0.5, self.timer_callback)
        self.get_logger().info('Turtle Ctrl Node has been started.')

    def timer_callback(self):
        msg = Twist()
        # 设置线速度
        msg.linear.x = 2.0
        # 设置角速度
        msg.angular.z = 1.0
        # 发布消息
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: linear.x={msg.linear.x}, angular.z={msg.angular.z}')

def main(args=None):
    rclpy.init(args=args)
    node = TurtleCtrlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
