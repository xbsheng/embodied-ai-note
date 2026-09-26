import asyncio
import sys
import os

# 使用 mcp SDK (Model Context Protocol)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client():
    # 1. 定义 Server 参数
    # 获取当前工作目录下的 server 脚本路径
    server_script = os.path.join(os.getcwd(), "12_mcp_server_fastmcp.py")
    
    # 定义服务器启动参数
    server_params = StdioServerParameters(
        command="python", 
        args=[server_script],
        env=None
    )

    print(f"正在连接 MCP Server: {server_script} ...")

    # 2. 建立 stdio 连接上下文
    async with stdio_client(server_params) as (read, write):
        # 3. 创建 Client Session
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            print("连接已建立！")

            # 4. 列出可用工具
            tools_result = await session.list_tools()
            print(f"\n发现 {len(tools_result.tools)} 个工具:")
            for tool in tools_result.tools:
                print(f"- {tool.name}: {tool.description}")

            # 5. 调用 'add' 工具
            print("\n正在调用 'add' 工具计算 10 + 20 ...")
            try:
                # 注意: call_tool 返回的是 CallToolResult 对象
                result = await session.call_tool("add", arguments={"a": 10, "b": 20})
                
                # 遍历结果内容
                # result.content 是 Content 对象的列表 (TextContent 或 ImageContent)
                for content in result.content:
                    if content.type == "text":
                        print(f"计算结果: {content.text}")
                    else:
                        print(f"收到非文本结果: {content}")
                        
            except Exception as e:
                print(f"调用工具失败: {e}")

if __name__ == "__main__":
    # Windows 上通常需要设置事件循环策略以支持子进程通信
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(run_client())
    except ImportError:
        print("错误: 未找到 mcp 库")
        print("请先安装: pip install mcp")
    except Exception as e:
        print(f"发生错误: {e}")
