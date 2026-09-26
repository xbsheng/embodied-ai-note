import rclpy
from rclpy.node import Node
from arm_msg.msg import ArmJointAngles
from arm_msg.srv import RecordControl
import csv
import os
import time
import threading
from enum import Enum

class NodeState(Enum):
    IDLE = 0
    RECORDING = 1
    PLAYBACK = 2

class ArmRecordPlaybackNode(Node):
    def __init__(self):
        super().__init__('arm_record_playback_node')
        self.get_logger().info('Arm Record/Playback Node has been started.')
        
        # State
        self.state = NodeState.IDLE
        self.state_lock = threading.Lock()
        
        # Recording attributes
        self.csv_file = None
        self.csv_writer = None
        self.record_count = 0
        self.file_path = ""
        
        # Playback attributes
        self.playback_thread = None
        self.stop_event = threading.Event()
        
        # Subscriber for recording
        self.subscription = self.create_subscription(
            ArmJointAngles,
            'arm_joint_angles',
            self.record_callback,
            10)
            
        # Publisher for playback
        self.publisher_ = self.create_publisher(ArmJointAngles, 'cmd_angles', 10)
        
        # Service for control
        self.srv = self.create_service(RecordControl, 'cmd_manager', self.control_callback)
        self.get_logger().info('Service cmd_manager is ready.')
        self.get_logger().info('Actions: record_start, record_stop, playback_start, playback_stop, status')

    def control_callback(self, request, response):
        action = request.action.lower()
        filename = request.filename
        
        with self.state_lock:
            current_state = self.state
        
        if action == 'record_start':
            if current_state != NodeState.IDLE:
                response.success = False
                response.message = f"Cannot start recording. Current state: {current_state.name}"
            else:
                success, msg = self.start_recording(filename)
                response.success = success
                response.message = msg
                
        elif action == 'record_stop':
            if current_state != NodeState.RECORDING:
                response.success = False
                response.message = "Not currently recording."
            else:
                success, msg = self.stop_recording()
                response.success = success
                response.message = msg
                
        elif action == 'playback_start':
            if current_state != NodeState.IDLE:
                response.success = False
                response.message = f"Cannot start playback. Current state: {current_state.name}"
            else:
                success, msg = self.start_playback(filename)
                response.success = success
                response.message = msg
                
        elif action == 'playback_stop':
            if current_state != NodeState.PLAYBACK:
                response.success = False
                response.message = "Not currently playing."
            else:
                success, msg = self.stop_playback()
                response.success = success
                response.message = msg
                
        elif action == 'status' or action == 'query':
            response.success = True
            details = ""
            if current_state == NodeState.RECORDING:
                details = f"(File: {os.path.basename(self.file_path)}, Count: {self.record_count})"
            elif current_state == NodeState.PLAYBACK:
                details = f"(File: {os.path.basename(self.file_path)})"
            response.message = f"State: {current_state.name} {details}"
            
        else:
            response.success = False
            response.message = f"Unknown action: {action}. Use record_start, record_stop, playback_start, playback_stop, status."
            
        return response

    # --- Recording Methods ---
    def start_recording(self, filename):
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
            
            self.record_count = 0
            with self.state_lock:
                self.state = NodeState.RECORDING
            
            self.get_logger().info(f"Started recording to {filename}")
            return True, f"Started recording to {filename}"
        except Exception as e:
            self.get_logger().error(f"Failed to open file: {str(e)}")
            return False, f"Failed to open file: {str(e)}"

    def stop_recording(self):
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
        
        with self.state_lock:
            self.state = NodeState.IDLE
            
        self.get_logger().info(f"Stopped recording. Saved {self.record_count} points.")
        return True, f"Stopped recording. Saved {self.record_count} points."

    def record_callback(self, msg):
        # Check state without lock for performance, but strictly it should be locked. 
        # Given Python GIL, simple read is atomic enough for this logic check.
        if self.state != NodeState.RECORDING:
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

    # --- Playback Methods ---
    def start_playback(self, filename):
        if not filename:
            filename = 'arm_trajectory.csv'
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
            
        self.file_path = file_path
        self.stop_event.clear()
        
        with self.state_lock:
            self.state = NodeState.PLAYBACK
            
        self.playback_thread = threading.Thread(target=self.playback_thread_func, args=(file_path,))
        self.playback_thread.start()
        
        self.get_logger().info(f"Started playback from {filename}")
        return True, f"Started playback from {filename}"

    def stop_playback(self):
        self.stop_event.set()
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join()
        
        # State reset is handled in thread or here? 
        # Safer to ensure it's reset here if thread finishes.
        # But thread might self-terminate.
        # Let's let the thread reset state when it finishes naturally, 
        # but if we force stop, we wait for join then reset.
        
        with self.state_lock:
            self.state = NodeState.IDLE
            
        self.get_logger().info("Stopped playback.")
        return True, "Stopped playback."

    def playback_thread_func(self, file_path):
        self.get_logger().info(f"Loading trajectory from {file_path}...")
        
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
                self.get_logger().warn("File is empty or invalid.")
                with self.state_lock:
                    self.state = NodeState.IDLE
                return

            self.get_logger().info(f"Loaded {len(data_points)} points. Starting playback...")
            
            start_time = time.time()
            record_start_time = data_points[0][0]
            
            for i, (rec_time, angles) in enumerate(data_points):
                if self.stop_event.is_set():
                    break
                
                target_delay = rec_time - record_start_time
                current_delay = time.time() - start_time
                sleep_time = target_delay - current_delay
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                msg = ArmJointAngles()
                msg.angles = angles
                self.publisher_.publish(msg)
            
            self.get_logger().info("Playback finished.")

        except Exception as e:
            self.get_logger().error(f"Error during playback: {e}")
        finally:
            with self.state_lock:
                self.state = NodeState.IDLE
            self.stop_event.clear()

    def destroy_node(self):
        self.stop_recording()
        self.stop_playback()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ArmRecordPlaybackNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
