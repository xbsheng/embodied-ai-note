import rclpy
from rclpy.node import Node
import asyncio
import sys
import os
import pyaudio
import wave
import threading
import whisper
import json
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ----------------- 配置参数 -----------------
# 录音配置
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
WAVE_OUTPUT_FILENAME = "input_command.wav"

# Whisper 配置
WHISPER_MODEL_TYPE = "base"

# DeepSeek 配置
API_KEY = 'sk-a80719c8b9cc4c708195d7f84fdd4a70'
BASE_URL = "https://api.deepseek.com"

# ----------------- 1. 录音模块 -----------------
class AudioRecorder:
    def __init__(self, logger):
        self.is_recording = False
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.record_thread = None
        self.logger = logger

    def _record(self):
        try:
            self.stream = self.p.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK)
            self.logger.info("正在录音... (输入 S 停止)")
            while self.is_recording:
                data = self.stream.read(CHUNK)
                self.frames.append(data)
            
            self.stream.stop_stream()
            self.stream.close()
        except Exception as e:
            self.logger.error(f"Error during recording: {e}")

    def start_recording(self):
        if self.is_recording: return
        self.frames = []
        self.is_recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()
        self.logger.info(">>> 开始录音")

    def stop_recording(self):
        if not self.is_recording: return
        self.logger.info(">>> 停止录音...")
        self.is_recording = False
        if self.record_thread:
            self.record_thread.join()
        
        return self.save_file()

    def save_file(self):
        if not self.frames: return None
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        self.logger.info(f"音频已保存到 {WAVE_OUTPUT_FILENAME}")
        return WAVE_OUTPUT_FILENAME

    def close(self):
        self.p.terminate()

# ----------------- 2. 语音识别模块 -----------------
def transcribe_audio(audio_file, logger):
    if not os.path.exists(audio_file):
        return None
    logger.info(f"正在加载 Whisper 模型 ('{WHISPER_MODEL_TYPE}')...")
    try:
        model = whisper.load_model(WHISPER_MODEL_TYPE)
        logger.info(f"正在识别...")
        result = model.transcribe(audio_file, fp16=False)
        text = result["text"].strip()
        logger.info(f"识别结果: {text}")
        return text
    except Exception as e:
        logger.error(f"识别出错: {e}")
        return None

# ----------------- 3. Agent Node Logic -----------------
class LLMAgentNode(Node):
    def __init__(self):
        super().__init__('llm_agent_node')
        self.get_logger().info('LLM Agent Node has been started.')
        self.recorder = AudioRecorder(self.get_logger())
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_async_loop, daemon=True)
        self.thread.start()

    def start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run_agent())

    async def run_agent(self):
        # 动态获取 mcp_server_node 的命令
        # 假设我们通过 ros2 run AI_pkg mcp_server_node 启动
        # 这里为了演示，我们直接假设用户已经启动了该节点或者我们通过 subprocess 启动它作为 MCP server
        # 但是 MCP 通常通过 stdio 通信，所以我们需要启动该脚本作为子进程
        
        # 寻找 mcp_server_node.py 的路径
        import pkg_resources
        # 由于我们是在开发环境，我们尝试直接定位源文件或者通过 ros2 run 命令
        # 为了简单起见，我们假设 mcp_server_node.py 就在同一包下，但 installed path 不同
        # 更好的方式是直接运行 python 脚本
        
        # 尝试查找 install 目录下的脚本
        # 或者直接使用 ros2 run 的命令格式（需要 fastmcp 支持，或者我们直接调用 python 脚本）
        # 这里我们假设使用 installed 的 python 脚本
        # 我们可以用 `ros2 pkg prefix AI_pkg` 找到包路径
        
        from ament_index_python.packages import get_package_prefix
        pkg_prefix = get_package_prefix('AI_pkg')
        # 在 install/AI_pkg/lib/AI_pkg/mcp_server_node
        mcp_server_script = os.path.join(pkg_prefix, 'lib', 'AI_pkg', 'mcp_server_node')
        
        self.get_logger().info(f"准备连接 MCP Server: {mcp_server_script}")
        
        # 注意：mcp_server_node 是一个 entry point script，可以直接执行
        server_params = StdioServerParameters(
            command=mcp_server_script,
            args=[],
            env=os.environ.copy()
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.get_logger().info("MCP Server 连接成功！")

                    # 获取可用工具
                    mcp_tools = await session.list_tools()
                    openai_tools = []
                    
                    # 转换工具格式为 OpenAI 兼容格式
                    self.get_logger().info(f"发现 {len(mcp_tools.tools)} 个 MCP 工具，正在注册到 DeepSeek...")
                    for tool in mcp_tools.tools:
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema
                            }
                        })
                        self.get_logger().info(f" - 已注册工具: {tool.name}")

                    print("\n=== 语音 MCP Agent 就绪 ===")
                    print("请按 'R' 开始录音，'S' 停止并发送指令 (例如：'帮我计算100加200')")
                    print("输入 'Q' 退出")

                    # 主交互循环
                    while rclpy.ok():
                        # 使用 run_in_executor 在 asyncio 中处理阻塞的 input
                        cmd = await self.loop.run_in_executor(None, input, "\n请输入指令 (R/S/Q): ")
                        cmd = cmd.strip().upper()

                        if cmd == 'R':
                            self.recorder.start_recording()
                        
                        elif cmd == 'S':
                            if not self.recorder.is_recording:
                                self.get_logger().info("请先按 R 开始录音")
                                continue
                                
                            audio_file = self.recorder.stop_recording()
                            
                            if audio_file:
                                # 1. 语音转文本
                                user_query = await self.loop.run_in_executor(None, transcribe_audio, audio_file, self.get_logger())
                                
                                if user_query:
                                    # 2. 调用 DeepSeek (附带工具定义)
                                    self.get_logger().info(f"正在请求 DeepSeek (Query: {user_query})...")
                                    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
                                    
                                    try:
                                        response = await self.loop.run_in_executor(None, lambda: client.chat.completions.create(
                                            model="deepseek-chat",
                                            messages=[
                                                {"role": "system", "content": "You are a helpful assistant. Use the provided tools to answer user questions if needed."},
                                                {"role": "user", "content": user_query}
                                            ],
                                            tools=openai_tools,
                                            stream=False
                                        ))
                                        
                                        message = response.choices[0].message
                                        
                                        # 3. 检查是否有工具调用
                                        if message.tool_calls:
                                            self.get_logger().info(f"DeepSeek 请求调用工具: {len(message.tool_calls)} 个")
                                            
                                            for tool_call in message.tool_calls:
                                                func_name = tool_call.function.name
                                                func_args = json.loads(tool_call.function.arguments)
                                                
                                                self.get_logger().info(f">>> 正在调用本地 MCP 工具: {func_name}({func_args})")
                                                
                                                # 4. 执行 MCP 工具
                                                result = await session.call_tool(func_name, arguments=func_args)
                                                
                                                # 打印结果
                                                for content in result.content:
                                                    if content.type == "text":
                                                        self.get_logger().info(f"<<< 工具执行结果: {content.text}")
                                                    else:
                                                        self.get_logger().info(f"<<< 工具执行结果(非文本): {content}")
                                        else:
                                            self.get_logger().info(f"DeepSeek 直接回复: {message.content}")
                                            
                                    except Exception as e:
                                        self.get_logger().error(f"DeepSeek 请求失败: {e}")

                        elif cmd == 'Q':
                            break
                            
        except Exception as e:
            self.get_logger().error(f"MCP 连接或执行错误: {e}")
        finally:
            self.recorder.close()
            # rclpy.shutdown() # Don't shutdown here, let main handle it or user interrupt

def main(args=None):
    rclpy.init(args=args)
    node = LLMAgentNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
