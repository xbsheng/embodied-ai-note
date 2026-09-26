import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from arm_msg.msg import ArmJointAngles
import csv
import os
import time
import threading

class RobotNodNode(Node):
    def __init__(self):
        super().__init__('robot_nod_node')
        self.get_logger().info('Robot Nod Node has been started.')
        
        # Subscribe to the trigger topic
        self.subscription = self.create_subscription(
            String,
            'robot_nod_trigger',
            self.nod_callback,
            10)
            
        # Publisher for arm angles
        self.publisher_ = self.create_publisher(ArmJointAngles, 'cmd_angles', 10)
        
        # Lock for playback safety
        self.playback_lock = threading.Lock()
        self.is_playing = False
        
        # Ensure nod trajectory file exists
        self.nod_filename = 'nod_trajectory.csv'
        self.ensure_nod_file_exists()

    def ensure_nod_file_exists(self):
        file_path = os.path.join(os.getcwd(), self.nod_filename)
        if not os.path.exists(file_path):
            self.get_logger().info(f"Creating default nod trajectory file at {file_path}")
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    header = ['timestamp', 'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
                    writer.writerow(header)
                    # Create a simple nod motion (assuming joint 4 is pitch)
                    # Time, J1, J2, J3, J4, J5, J6
                    writer.writerow([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                    writer.writerow([0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0]) # Nod down/up
                    writer.writerow([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) # Return
            except Exception as e:
                self.get_logger().error(f"Failed to create nod file: {e}")

    def nod_callback(self, msg):
        self.get_logger().info(f"Received nod trigger: {msg.data}")
        if not self.is_playing:
            threading.Thread(target=self.play_nod_trajectory).start()
        else:
            self.get_logger().warn("Already nodding, ignoring request.")

    def play_nod_trajectory(self):
        with self.playback_lock:
            self.is_playing = True
        
        file_path = os.path.join(os.getcwd(), self.nod_filename)
        self.get_logger().info(f"Starting nod playback from {file_path}...")
        
        try:
            data_points = []
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader) # Skip header
                for row in reader:
                    if not row: continue
                    timestamp = float(row[0])
                    angles = [float(x) for x in row[1:7]]
                    data_points.append((timestamp, angles))
            
            if not data_points:
                self.get_logger().warn("Nod file is empty.")
                return

            start_time = time.time()
            record_start_time = data_points[0][0]
            
            for rec_time, angles in data_points:
                target_delay = rec_time - record_start_time
                current_delay = time.time() - start_time
                sleep_time = target_delay - current_delay
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                msg = ArmJointAngles()
                msg.angles = angles
                self.publisher_.publish(msg)
                
            self.get_logger().info("Nod playback finished.")

        except Exception as e:
            self.get_logger().error(f"Error during nod playback: {e}")
        finally:
            with self.playback_lock:
                self.is_playing = False

def main(args=None):
    rclpy.init(args=args)
    node = RobotNodNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
