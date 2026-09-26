import sys
import rclpy
from rclpy.node import Node
from arm_msg.srv import RecordControl
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSlot

class RecordPlaybackClient(Node):
    def __init__(self):
        super().__init__('gui_record_playback_node')
        self.client = self.create_client(RecordControl, 'cmd_manager')
        
        # Wait for service (non-blocking check in GUI loop is better, but simple check here)
        # We won't block here to avoid freezing GUI startup, handled in logic.
        
        self.current_status_future = None
        self.command_future = None
        self.latest_status_message = "Connecting..."
        self.latest_state_str = "UNKNOWN"

    def send_command(self, action, filename=""):
        if not self.client.wait_for_service(timeout_sec=1.0):
            return False, "Service not available"
            
        req = RecordControl.Request()
        req.action = action
        req.filename = filename
        
        # Async call
        self.command_future = self.client.call_async(req)
        # We attach a callback to handle the response? 
        # In this pattern, we will check future completion in the GUI timer loop 
        # or let the spin loop handle it.
        # But we need the result in the GUI. 
        return True, "Request sent"

    def check_status(self):
        # Poll status
        if self.client.service_is_ready():
            req = RecordControl.Request()
            req.action = 'status'
            self.current_status_future = self.client.call_async(req)

class RecordPlaybackWindow(QWidget):
    def __init__(self, ros_node):
        super().__init__()
        self.ros_node = ros_node
        self.init_ui()
        
        # Timer for ROS spinning
        self.ros_timer = QTimer(self)
        self.ros_timer.timeout.connect(self.spin_ros)
        self.ros_timer.start(10) # 100Hz
        
        # Timer for Status Polling
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.poll_status)
        self.status_timer.start(500) # 2Hz

    def init_ui(self):
        self.setWindowTitle('Arm Record & Playback Control')
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # File Name Input
        file_layout = QHBoxLayout()
        file_label = QLabel('Filename:')
        self.file_input = QLineEdit('arm_trajectory.csv')
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_input)
        layout.addLayout(file_layout)
        
        # Recording Controls
        rec_layout = QHBoxLayout()
        self.btn_start_rec = QPushButton('Start Recording')
        self.btn_start_rec.clicked.connect(self.on_start_rec)
        self.btn_start_rec.setStyleSheet("background-color: #ffcccc;")
        
        self.btn_stop_rec = QPushButton('Stop Recording')
        self.btn_stop_rec.clicked.connect(self.on_stop_rec)
        self.btn_stop_rec.setEnabled(False)
        
        rec_layout.addWidget(self.btn_start_rec)
        rec_layout.addWidget(self.btn_stop_rec)
        layout.addLayout(rec_layout)
        
        # Playback Controls
        play_layout = QHBoxLayout()
        self.btn_start_play = QPushButton('Start Playback')
        self.btn_start_play.clicked.connect(self.on_start_play)
        self.btn_start_play.setStyleSheet("background-color: #ccffcc;")
        
        self.btn_stop_play = QPushButton('Stop Playback')
        self.btn_stop_play.clicked.connect(self.on_stop_play)
        self.btn_stop_play.setEnabled(False)
        
        play_layout.addWidget(self.btn_start_play)
        play_layout.addWidget(self.btn_stop_play)
        layout.addLayout(play_layout)
        
        # Status Display
        self.status_label = QLabel('Status: Waiting for service...')
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-weight: bold; border: 1px solid gray; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)

    def spin_ros(self):
        # Spin ROS node once
        rclpy.spin_once(self.ros_node, timeout_sec=0)
        
        # Check command future
        if self.ros_node.command_future and self.ros_node.command_future.done():
            try:
                result = self.ros_node.command_future.result()
                # We can show a temporary message or just rely on status update
                # print(f"Command result: {result.success} - {result.message}")
                if not result.success:
                     QMessageBox.warning(self, "Error", result.message)
            except Exception as e:
                print(f"Command failed: {e}")
            self.ros_node.command_future = None

        # Check status future
        if self.ros_node.current_status_future and self.ros_node.current_status_future.done():
            try:
                result = self.ros_node.current_status_future.result()
                self.update_ui_state(result.message)
            except Exception as e:
                self.status_label.setText(f"Status Error: {str(e)}")
            self.ros_node.current_status_future = None

    def poll_status(self):
        self.ros_node.check_status()

    def update_ui_state(self, status_msg):
        self.status_label.setText(status_msg)
        
        # Parse status message to determine state
        # Expected format: "State: RECORDING (File: ...)" or "State: IDLE"
        
        is_recording = "State: RECORDING" in status_msg
        is_playback = "State: PLAYBACK" in status_msg
        is_idle = "State: IDLE" in status_msg
        
        if is_recording:
            self.btn_start_rec.setEnabled(False)
            self.btn_stop_rec.setEnabled(True)
            self.btn_start_play.setEnabled(False)
            self.btn_stop_play.setEnabled(False)
            self.file_input.setEnabled(False)
            
        elif is_playback:
            self.btn_start_rec.setEnabled(False)
            self.btn_stop_rec.setEnabled(False)
            self.btn_start_play.setEnabled(False)
            self.btn_stop_play.setEnabled(True)
            self.file_input.setEnabled(False)
            
        else: # IDLE or Unknown
            self.btn_start_rec.setEnabled(True)
            self.btn_stop_rec.setEnabled(False)
            self.btn_start_play.setEnabled(True)
            self.btn_stop_play.setEnabled(False)
            self.file_input.setEnabled(True)

    def on_start_rec(self):
        filename = self.file_input.text()
        self.ros_node.send_command('record_start', filename)

    def on_stop_rec(self):
        self.ros_node.send_command('record_stop')

    def on_start_play(self):
        filename = self.file_input.text()
        self.ros_node.send_command('playback_start', filename)

    def on_stop_play(self):
        self.ros_node.send_command('playback_stop')

def main(args=None):
    rclpy.init(args=args)
    
    app = QApplication(sys.argv)
    ros_node = RecordPlaybackClient()
    
    window = RecordPlaybackWindow(ros_node)
    window.show()
    
    try:
        sys.exit(app.exec_())
    except Exception:
        pass
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
