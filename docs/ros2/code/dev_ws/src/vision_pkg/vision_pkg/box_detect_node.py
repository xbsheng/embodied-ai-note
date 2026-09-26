import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
import cv2
import numpy as np

class BoxDetectNode(Node):
    def __init__(self):
        super().__init__('box_detect_node')
        self.get_logger().info('Box Detect Node has been started.')
        
        # ==========================================
        # Configuration Section (方便配置的区域)
        # ==========================================
        # HSV Thresholds (HSV 阈值)
        self.hue_min = 90
        self.hue_max = 120
        self.sat_min = 94
        self.sat_max = 192
        self.val_min = 109
        self.val_max = 255
        
        # Morphological Operations (形态学操作)
        self.erode_iter = 1    # 腐蚀迭代次数
        self.dilate_iter = 1   # 膨胀迭代次数
        
        # Filter (过滤)
        self.min_area = 1000   # 最小面积
        # ==========================================

        # Subscribe to image topic
        self.subscription = self.create_subscription(
            Image,
            'image_raw',
            self.listener_callback,
            10)
        self.subscription
        
        # Publisher for box info (cx, cy, width, height)
        self.publisher_ = self.create_publisher(Float32MultiArray, 'box_info', 10)
        
        self.bridge = CvBridge()
        
        # No GUI for parameters needed, only display windows
        # cv2.namedWindow("Mask")
        # cv2.namedWindow("Result")

    def listener_callback(self, msg):
        try:
            # Convert ROS Image to OpenCV Image
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # Create a copy for drawing
            imgContour = frame.copy()

            # Preprocessing
            imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Use Fixed Configuration Values
            h_min = self.hue_min
            h_max = self.hue_max
            s_min = self.sat_min
            s_max = self.sat_max
            v_min = self.val_min
            v_max = self.val_max
            
            erode_iter = self.erode_iter
            dilate_iter = self.dilate_iter
            min_area = self.min_area

            # Create Mask
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(imgHSV, lower, upper)

            # Morphological Operations
            kernel = np.ones((5, 5), np.uint8)
            if erode_iter > 0:
                mask = cv2.erode(mask, kernel, iterations=erode_iter)
            if dilate_iter > 0:
                mask = cv2.dilate(mask, kernel, iterations=dilate_iter)

            # Find Contours
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > min_area:
                    # Calculate bounding box
                    peri = cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                    x, y, w, h = cv2.boundingRect(approx)

                    # Draw red bounding box
                    cv2.rectangle(imgContour, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    # Calculate center
                    cx = x + w // 2
                    cy = y + h // 2

                    # Draw green center point
                    cv2.circle(imgContour, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

                    # Put text: Center and Size
                    cv2.putText(imgContour, f"Pos:({cx}, {cy})", (x, y - 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    cv2.putText(imgContour, f"Size:({w}x{h})", (x, y - 5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                    
                    # Publish the box info
                    msg = Float32MultiArray()
                    msg.data = [float(cx), float(cy), float(w), float(h)]
                    self.publisher_.publish(msg)
                    # self.get_logger().info(f'Published box info: {msg.data}')

            # Display
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
    node = BoxDetectNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
