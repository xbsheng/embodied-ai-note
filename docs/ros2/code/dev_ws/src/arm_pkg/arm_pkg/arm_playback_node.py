import rclpy
from rclpy.node import Node
from arm_msg.msg import ArmJointAngles
from arm_msg.srv import RecordControl
import csv
import os
import time
import threading

class ArmPlaybackNode(Node):
    def __init__(self):
        super().__init__('arm_playback_node')
        self.get_logger().info('Arm Playback Node has been started.')
        
        # State
        self.is_playing = False
        self.playback_thread = None
        self.stop_event = threading.Event()
        
        # Publisher to arm_joint_angles topic (or cmd_angles as per requirement to drive the arm)
        # The user said: "broadcast call the driver node ... arm_joint_node.py's joint drive function"
        # arm_joint_node subscribes to 'cmd_angles'
        self.publisher_ = self.create_publisher(ArmJointAngles, 'cmd_angles', 10)
        
        # Create Service for control
        self.srv = self.create_service(RecordControl, 'cmd_playback', self.playback_control_callback)
        self.get_logger().info('Service cmd_playback is ready. Use "start" (with filename) or "stop".')

    def playback_control_callback(self, request, response):
        action = request.action.lower()
        
        if action == 'start':
            if self.is_playing:
                response.success = False
                response.message = "Already playing."
            else:
                filename = request.filename
                if not filename:
                    filename = 'arm_trajectory.csv'
                if not filename.endswith('.csv'):
                    filename += '.csv'
                
                file_path = os.path.join(os.getcwd(), filename)
                if not os.path.exists(file_path):
                    response.success = False
                    response.message = f"File not found: {file_path}"
                else:
                    self.stop_event.clear()
                    self.playback_thread = threading.Thread(target=self.playback_thread_func, args=(file_path,))
                    self.playback_thread.start()
                    
                    response.success = True
                    response.message = f"Started playback from {filename}"
                    self.get_logger().info(response.message)
                    
        elif action == 'stop':
            if not self.is_playing:
                response.success = False
                response.message = "Not currently playing."
            else:
                self.stop_event.set()
                if self.playback_thread:
                    self.playback_thread.join()
                response.success = True
                response.message = "Stopped playback."
                self.get_logger().info(response.message)
                
        else:
            response.success = False
            response.message = f"Unknown action: {action}. Use 'start' or 'stop'."
            
        return response

    def playback_thread_func(self, file_path):
        self.is_playing = True
        self.get_logger().info(f"Loading trajectory from {file_path}...")
        
        try:
            data_points = []
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader) # Skip header
                for row in reader:
                    if not row: continue
                    # timestamp, j1, j2, j3, j4, j5, j6
                    timestamp = float(row[0])
                    angles = [float(x) for x in row[1:7]]
                    data_points.append((timestamp, angles))
            
            if not data_points:
                self.get_logger().warn("File is empty or invalid.")
                self.is_playing = False
                return

            self.get_logger().info(f"Loaded {len(data_points)} points. Starting playback...")
            
            start_time = time.time()
            record_start_time = data_points[0][0]
            
            for i, (rec_time, angles) in enumerate(data_points):
                if self.stop_event.is_set():
                    break
                
                # Calculate how much time has passed in the recording relative to start
                target_delay = rec_time - record_start_time
                
                # Calculate how much time has passed in real life
                current_delay = time.time() - start_time
                
                # Sleep if we are ahead of schedule
                sleep_time = target_delay - current_delay
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Publish
                msg = ArmJointAngles()
                msg.angles = angles
                self.publisher_.publish(msg)
                
                # Log occasionally
                if i % 10 == 0:
                    # self.get_logger().info(f"Replaying frame {i}/{len(data_points)}")
                    pass

            self.get_logger().info("Playback finished.")

        except Exception as e:
            self.get_logger().error(f"Error during playback: {e}")
        finally:
            self.is_playing = False

    def destroy_node(self):
        self.stop_event.set()
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ArmPlaybackNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
