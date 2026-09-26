import sys
from fastmcp import FastMCP

# 1. 创建 MCP Server 实例
# "Math Server" 是服务的名称
mcp = FastMCP("Math Server")

# 2. 定义工具 (Tool)
# @mcp.tool() 装饰器会将函数注册为 MCP 工具
# 类型提示 (Type Hints) 和文档字符串 (Docstrings) 非常重要，
# 它们会被转换为工具的 Schema 供 LLM 理解
@mcp.tool()
def add(a: int, b: int) -> int:
    """
    计算两个整数的和 (Add two integers)
    
    Args:
        a: 第一个加数
        b: 第二个加数
        
    Returns:
        两数之和
    """
    result = a + b
    print(f"Executing add({a}, {b}) -> {result}") # 日志会输出到 stderr
    return result

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """
    计算两个整数的差 (Subtract two integers)
    
    Args:
        a: 被减数
        b: 减数
        
    Returns:
        两数之差 (a - b)
    """
    result = a - b
    print(f"Executing subtract({a}, {b}) -> {result}")
    return result

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """
    计算两个整数的积 (Multiply two integers)
    
    Args:
        a: 第一个乘数
        b: 第二个乘数
        
    Returns:
        两数之积
    """
    result = a * b
    print(f"Executing multiply({a}, {b}) -> {result}")
    return result

@mcp.tool()
def divide(a: int, b: int) -> float:
    """
    计算两个整数的商 (Divide two integers)
    
    Args:
        a: 被除数
        b: 除数 (不能为0)
        
    Returns:
        两数之商
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    result = a / b
    print(f"Executing divide({a}, {b}) -> {result}")
    return result

@mcp.tool()
def robot_nod() -> str:
    """
    控制机械臂执行点头动作 (Make the robot arm nod)
    此工具不接受参数，仅执行预设的动作序列。
    
    Returns:
        执行结果消息
    """
    print("Executing robot_nod()...")
    print("LOG: Robot Arm Moving: Position 0 -> Position 1 (Nod Down)")
    print("LOG: Robot Arm Moving: Position 1 -> Position 0 (Nod Up)")
    return "Robot arm nodded successfully."

# 3. 运行 Server
# 默认情况下，mcp.run() 会使用 stdio 传输协议
if __name__ == "__main__":
    print("MCP Server is running...", file=sys.stderr)
    mcp.run()
