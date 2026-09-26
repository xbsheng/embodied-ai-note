import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class CameraNativeNode(Node):
    def __init__(self):
        super().__init__('camera_native_node')
        self.get_logger().info('Camera Native Node has been started.')
        
        # Subscribe to the camera topic
        # Defaulting to 'image_raw', but usually cameras might use other topics.
        # This can be remapped or parameterized.
        self.subscription = self.create_subscription(
            Image,
            'image_raw',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        
        self.bridge = CvBridge()
        self.window_name = "Camera Feed"

    def listener_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # Display the image
            cv2.imshow(self.window_name, cv_image)
            
            # Wait for 1ms to process GUI events
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f'Failed to convert/display image: {str(e)}')

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CameraNativeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
