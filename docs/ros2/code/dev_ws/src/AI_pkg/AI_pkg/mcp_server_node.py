import rclpy
from rclpy.node import Node
import threading
import sys
from fastmcp import FastMCP

from std_msgs.msg import String

# Global node reference for tools to access ROS logging/publishers
NODE_REF = None

# 1. Create MCP Server Instance
mcp = FastMCP("ROS2 MCP Server")

# 2. Define Tools
@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two integers
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        Sum of a and b
    """
    result = a + b
    log(f"Executing add({a}, {b}) -> {result}")
    return result

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """
    Subtract two integers
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        Difference (a - b)
    """
    result = a - b
    log(f"Executing subtract({a}, {b}) -> {result}")
    return result

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """
    Multiply two integers
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        Product of a and b
    """
    result = a * b
    log(f"Executing multiply({a}, {b}) -> {result}")
    return result

@mcp.tool()
def divide(a: int, b: int) -> float:
    """
    Divide two integers
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        Quotient (a / b)
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    result = a / b
    log(f"Executing divide({a}, {b}) -> {result}")
    return result

@mcp.tool()
def robot_nod() -> str:
    """
    Make the robot arm nod
    
    Returns:
        Execution result message
    """
    log("Executing robot_nod()...")
    if NODE_REF:
        msg = String()
        msg.data = "nod"
        NODE_REF.nod_publisher.publish(msg)
        log("Published nod trigger to /robot_nod_trigger")
        return "Robot arm nod triggered."
    else:
        return "Error: ROS node reference not available."

def log(msg):
    """Helper to log to ROS logger if available, else stderr"""
    if NODE_REF:
        NODE_REF.get_logger().info(msg)
    else:
        print(msg, file=sys.stderr)

class MCPServerNode(Node):
    def __init__(self):
        super().__init__('mcp_server_node')
        self.get_logger().info('MCP Server Node has been started.')
        
        # Publisher for robot nod trigger
        self.nod_publisher = self.create_publisher(String, 'robot_nod_trigger', 10)
        
        global NODE_REF
        NODE_REF = self

def main(args=None):
    rclpy.init(args=args)
    node = MCPServerNode()
    
    # Run ROS spin in a separate thread so MCP can block main thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()
    
    try:
        print("MCP Server is running...", file=sys.stderr)
        # Run MCP server (blocks)
        mcp.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
