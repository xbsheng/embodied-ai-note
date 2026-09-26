import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

def empty(a):
    pass

class HSVImageNode(Node):
    def __init__(self):
        super().__init__('hsv_image_node')
        self.get_logger().info('HSV Image Node has been started.')
        
        # Subscribe to image topic
        self.subscription = self.create_subscription(
            Image,
            'image_raw',
            self.listener_callback,
            10)
        self.subscription
        
        self.bridge = CvBridge()
        
        # 初始化窗口和滑动条
        self.setup_interface()

    def setup_interface(self):
        cv2.namedWindow("Parameters")
        cv2.resizeWindow("Parameters", 640, 350)

        # 初始 HSV 阈值
        cv2.createTrackbar("Hue Min", "Parameters", 0, 179, empty)
        cv2.createTrackbar("Hue Max", "Parameters", 179, 179, empty)
        cv2.createTrackbar("Sat Min", "Parameters", 0, 255, empty)
        cv2.createTrackbar("Sat Max", "Parameters", 255, 255, empty)
        cv2.createTrackbar("Val Min", "Parameters", 0, 255, empty)
        cv2.createTrackbar("Val Max", "Parameters", 255, 255, empty)

        # 腐蚀和膨胀迭代次数
        cv2.createTrackbar("Erode Iter", "Parameters", 1, 10, empty)
        cv2.createTrackbar("Dilate Iter", "Parameters", 1, 10, empty)
        
        # 最小面积过滤
        cv2.createTrackbar("Min Area", "Parameters", 1000, 20000, empty)

    def listener_callback(self, msg):
        try:
            # 将 ROS 图像转换为 OpenCV 图像
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # 创建副本用于绘制
            imgContour = frame.copy()

            # 预处理
            imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # 获取滑动条的值
            h_min = cv2.getTrackbarPos("Hue Min", "Parameters")
            h_max = cv2.getTrackbarPos("Hue Max", "Parameters")
            s_min = cv2.getTrackbarPos("Sat Min", "Parameters")
            s_max = cv2.getTrackbarPos("Sat Max", "Parameters")
            v_min = cv2.getTrackbarPos("Val Min", "Parameters")
            v_max = cv2.getTrackbarPos("Val Max", "Parameters")
            erode_iter = cv2.getTrackbarPos("Erode Iter", "Parameters")
            dilate_iter = cv2.getTrackbarPos("Dilate Iter", "Parameters")
            min_area = cv2.getTrackbarPos("Min Area", "Parameters")

            # 创建掩膜 (Mask)
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(imgHSV, lower, upper)

            # 形态学操作
            kernel = np.ones((5, 5), np.uint8)
            if erode_iter > 0:
                mask = cv2.erode(mask, kernel, iterations=erode_iter)
            if dilate_iter > 0:
                mask = cv2.dilate(mask, kernel, iterations=dilate_iter)

            # 查找轮廓
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > min_area:
                    # 计算外接矩形
                    peri = cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                    x, y, w, h = cv2.boundingRect(approx)

                    # 绘制红色边界框
                    cv2.rectangle(imgContour, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    # 计算中心点
                    cx = x + w // 2
                    cy = y + h // 2

                    # 绘制绿色中心点
                    cv2.circle(imgContour, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

                    # 显示坐标
                    cv2.putText(imgContour, f"({cx}, {cy})", (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # 显示结果
            cv2.imshow("Mask", mask)
            cv2.imshow("Result", imgContour)
            
            cv2.waitKey(1)

        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = HSVImageNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
