import rclpy
from rclpy.node import Node
from arm_msg.msg import ArmJointAngles
import serial
import time
import sys

# --- ServoController Class ---
class ServoController:
    def __init__(self, port="/dev/ttyUSB0", baudrate=1000000, timeout=0.1):
        self.port_name = port
        self.serial_port = None
        # Constants
        self.ADDR_PRESENT_POSITION = 56
        self.ADDR_GOAL_POSITION = 42
        self.ADDR_TORQUE_ENABLE = 40
        self.INST_READ = 2
        self.INST_WRITE = 3
        self.COMM_SUCCESS = 0
        self.COMM_RX_TIMEOUT = -6
        self.COMM_RX_CORRUPT = -7
        
        try:
            self.serial_port = serial.Serial(port, baudrate=baudrate, timeout=timeout)
            time.sleep(0.1)
            self.serial_port.reset_input_buffer()
            # print(f"Successfully opened port {port}.")
        except serial.SerialException as e:
            pass
            # print(f"Fatal: Could not open port {port}: {e}")
            # sys.exit(1)

    def close(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def _calculate_checksum(self, data):
        return (~sum(data)) & 0xFF

    def _send_packet(self, servo_id, instruction, parameters=None):
        if not self.serial_port or not self.serial_port.is_open:
            return False
        if parameters is None:
            parameters = []
        length = len(parameters) + 2
        packet_core = [servo_id, length, instruction] + parameters
        checksum = self._calculate_checksum(packet_core)
        packet = bytes([0xFF, 0xFF] + packet_core + [checksum])
        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.write(packet)
            self.serial_port.flush()
            return True
        except Exception:
            return False

    def _read_packet(self):
        if not self.serial_port or not self.serial_port.is_open:
             return self.COMM_RX_TIMEOUT, 0, []
        start_time = time.time()
        packet = []
        while (time.time() - start_time) < self.serial_port.timeout:
            if self.serial_port.in_waiting > 0:
                byte = self.serial_port.read(1)
                if not byte: continue
                byte = byte[0]

                if not packet and byte != 0xFF:
                    continue
                
                packet.append(byte)

                if len(packet) >= 2 and packet[-2:] == [0xFF, 0xFF]:
                    if len(packet) > 2:
                        packet = [0xFF, 0xFF]
                    continue

                if len(packet) > 4:
                    pkt_len = packet[3]
                    if len(packet) == pkt_len + 4:
                        core_data = packet[2:-1]
                        calculated_checksum = self._calculate_checksum(core_data)
                        if calculated_checksum == packet[-1]:
                            return self.COMM_SUCCESS, packet[4], packet[5:-1]
                        else:
                            return self.COMM_RX_CORRUPT, 0, []
        return self.COMM_RX_TIMEOUT, 0, []

    def _write_register(self, servo_id, address, value, size=2):
        params = [address]
        if size == 1:
            params.append(value & 0xFF)
        elif size == 2:
            params.extend([value & 0xFF, (value >> 8) & 0xFF])
        else:
            return False
        
        if not self._send_packet(servo_id, self.INST_WRITE, params):
            return False
        
        return True

    def enable_torque(self, servo_id):
        return self._write_register(servo_id, self.ADDR_TORQUE_ENABLE, 1, size=1)

    def disable_torque(self, servo_id):
        return self._write_register(servo_id, self.ADDR_TORQUE_ENABLE, 0, size=1)

    def set_servo_angle(self, servo_id, angle):
        """Sets the servo to a specific angle (-90 to 90 degrees)."""
        # Map angle (-90 to 90) to position (1024 to 3072)
        position = int(((angle + 90.0) / 180.0) * (3072.0 - 1024.0) + 1024.0)
        # Clamp the value to be safe
        position = max(1024, min(3072, position))
        
        return self._write_register(servo_id, self.ADDR_GOAL_POSITION, position, size=2)

    def get_servo_angle(self, servo_id):
        if not self._send_packet(servo_id, self.INST_READ, [self.ADDR_PRESENT_POSITION, 2]):
            return None

        result, error, data = self._read_packet()

        if result != self.COMM_SUCCESS or error != 0:
            return None
        
        if data and len(data) >= 2:
            position = data[0] | (data[1] << 8)
            angle = ((position - 1024.0) / (3072.0 - 1024.0)) * 180.0 - 90.0
            angle = max(-90.0, min(90.0, angle))
            return angle
        return None

class ArmJointNode(Node):
    def __init__(self):
        super().__init__('arm_joint_node')
        self.get_logger().info('Arm Joint Node has been started.')
        
        # Initialize ServoController
        # Using /dev/ttyUSB0 as default for Linux
        self.controller = ServoController(port="/dev/ttyUSB0")
        if not self.controller.serial_port or not self.controller.serial_port.is_open:
             self.get_logger().warn('Failed to open serial port /dev/ttyUSB0. Running in dummy mode?')

        # Create a timer to read angles every 100ms
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.servo_ids = list(range(1, 7)) # Servos 1-6
        
        # Disable torque for all servos to allow manual movement
        for servo_id in self.servo_ids:
            self.controller.disable_torque(servo_id)
            time.sleep(0.05)
            
        self.publisher_ = self.create_publisher(ArmJointAngles, 'arm_joint_angles', 10)
        self.subscription_ = self.create_subscription(
            ArmJointAngles,
            'cmd_angles',
            self.listener_callback,
            10)
        self.subscription_  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(f'Received command angles: {msg.angles}')
        if len(msg.angles) != 6:
            self.get_logger().warn(f'Received invalid number of angles: {len(msg.angles)}. Expected 6.')
            return

        for i, angle in enumerate(msg.angles):
            servo_id = self.servo_ids[i]
            # Enable torque before moving
            self.controller.enable_torque(servo_id)
            # Ensure angle is float
            angle_val = float(angle)
            self.controller.set_servo_angle(servo_id, angle_val)

    def timer_callback(self):
        angles = []
        for servo_id in self.servo_ids:
            angle = self.controller.get_servo_angle(servo_id)
            if angle is not None:
                angles.append(angle)
            else:
                angles.append(0.0) # Default or error value
        
        msg = ArmJointAngles()
        msg.angles = [float(a) for a in angles]
        self.publisher_.publish(msg)
        # self.get_logger().info(f'Published Joint Angles: {angles}')

    def destroy_node(self):
        if hasattr(self, 'controller') and self.controller:
            self.controller.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ArmJointNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
