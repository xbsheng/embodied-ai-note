import rclpy
from rclpy.node import Node
from arm_msg.msg import ArmJointAngles
from arm_msg.srv import RecordControl
import csv
import os
import time

class ArmRecordNode(Node):
    def __init__(self):
        super().__init__('arm_record_node')
        self.get_logger().info('Arm Record Node has been started.')
        
        # State
        self.is_recording = False
        self.csv_file = None
        self.csv_writer = None
        self.record_count = 0
        self.file_path = ""
        
        # Subscribe to arm_joint_angles topic
        self.subscription = self.create_subscription(
            ArmJointAngles,
            'arm_joint_angles',
            self.listener_callback,
            10)
            
        # Create Service
        self.srv = self.create_service(RecordControl, 'cmd_record', self.record_control_callback)
        self.get_logger().info('Service cmd_record is ready. Use "start", "stop", or "query".')

    def record_control_callback(self, request, response):
        action = request.action.lower()
        
        if action == 'start':
            if self.is_recording:
                response.success = False
                response.message = "Already recording."
            else:
                # Start recording
                filename = request.filename
                if not filename:
                    filename = 'arm_trajectory.csv'
                if not filename.endswith('.csv'):
                    filename += '.csv'
                    
                self.file_path = os.path.join(os.getcwd(), filename)
                try:
                    self.csv_file = open(self.file_path, 'w', newline='')
                    self.csv_writer = csv.writer(self.csv_file)
                    header = ['timestamp', 'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
                    self.csv_writer.writerow(header)
                    
                    self.is_recording = True
                    self.record_count = 0
                    
                    response.success = True
                    response.message = f"Started recording to {filename}"
                    self.get_logger().info(response.message)
                except Exception as e:
                    response.success = False
                    response.message = f"Failed to open file: {str(e)}"
                    self.get_logger().error(response.message)
                    
        elif action == 'stop':
            if not self.is_recording:
                response.success = False
                response.message = "Not currently recording."
            else:
                self.close_file()
                response.success = True
                response.message = f"Stopped recording. Saved {self.record_count} points."
                self.get_logger().info(response.message)
                
        elif action == 'status' or action == 'query':
            response.success = True
            status_str = "Recording" if self.is_recording else "Idle"
            file_str = f" to {os.path.basename(self.file_path)}" if self.is_recording else ""
            response.message = f"Status: {status_str}{file_str}. Count: {self.record_count}"
            
        else:
            response.success = False
            response.message = f"Unknown action: {action}. Use 'start', 'stop', or 'query'."
            
        return response

    def close_file(self):
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
        self.is_recording = False

    def listener_callback(self, msg):
        if not self.is_recording:
            return
            
        if len(msg.angles) != 6:
            self.get_logger().warn(f'Received invalid number of angles: {len(msg.angles)}')
            return
            
        now = self.get_clock().now()
        timestamp = now.nanoseconds / 1e9
        row = [timestamp] + [float(angle) for angle in msg.angles]
        
        if self.csv_writer:
            self.csv_writer.writerow(row)
            self.record_count += 1
            
            if self.record_count % 10 == 0:
                self.get_logger().info(f'Recording... {self.record_count} points.')

    def destroy_node(self):
        self.close_file()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ArmRecordNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
