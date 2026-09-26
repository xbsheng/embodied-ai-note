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
WHISPER_MODEL_TYPE = "large"

# DeepSeek 配置
API_KEY = 'sk-a80719c8b9cc4c708195d7f84fdd4a70'
BASE_URL = "https://api.deepseek.com"

# MCP Server 路径
MCP_SERVER_SCRIPT = os.path.join(os.getcwd(), "12_mcp_server_fastmcp.py")

# ----------------- 1. 录音模块 -----------------
class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.record_thread = None

    def _record(self):
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)
        print("正在录音... (输入 S 停止)")
        while self.is_recording:
            data = self.stream.read(CHUNK)
            self.frames.append(data)
        
        self.stream.stop_stream()
        self.stream.close()

    def start_recording(self):
        if self.is_recording: return
        self.frames = []
        self.is_recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()
        print(">>> 开始录音")

    def stop_recording(self):
        if not self.is_recording: return
        print(">>> 停止录音...")
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
        print(f"音频已保存到 {WAVE_OUTPUT_FILENAME}")
        return WAVE_OUTPUT_FILENAME

    def close(self):
        self.p.terminate()

# ----------------- 2. 语音识别模块 -----------------
def transcribe_audio(audio_file):
    if not os.path.exists(audio_file):
        return None
    print(f"正在加载 Whisper 模型 ('{WHISPER_MODEL_TYPE}')...")
    try:
        model = whisper.load_model(WHISPER_MODEL_TYPE)
        print(f"正在识别...")
        result = model.transcribe(audio_file, fp16=False)
        text = result["text"].strip()
        print(f"识别结果: {text}")
        return text
    except Exception as e:
        print(f"识别出错: {e}")
        return None

# ----------------- 3. Agent 主逻辑 -----------------
async def run_agent():
    # 初始化录音器
    recorder = AudioRecorder()
    
    # 定义 MCP Server 连接参数
    print(f"准备连接 MCP Server: {MCP_SERVER_SCRIPT}")
    server_params = StdioServerParameters(
        command="python",
        args=[MCP_SERVER_SCRIPT],
        env=None
    )

    # 建立 MCP 连接
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("MCP Server 连接成功！")

            # 获取可用工具
            mcp_tools = await session.list_tools()
            openai_tools = []
            
            # 转换工具格式为 OpenAI 兼容格式
            print(f"发现 {len(mcp_tools.tools)} 个 MCP 工具，正在注册到 DeepSeek...")
            for tool in mcp_tools.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })
                print(f" - 已注册工具: {tool.name}")

            print("\n=== 语音 MCP Agent 就绪 ===")
            print("请按 'R' 开始录音，'S' 停止并发送指令 (例如：'帮我计算100加200')")
            print("输入 'Q' 退出")

            # 主交互循环
            while True:
                # 使用 run_in_executor 在 asyncio 中处理阻塞的 input
                loop = asyncio.get_running_loop()
                cmd = await loop.run_in_executor(None, input, "\n请输入指令 (R/S/Q): ")
                cmd = cmd.strip().upper()

                if cmd == 'R':
                    recorder.start_recording()
                
                elif cmd == 'S':
                    if not recorder.is_recording:
                        print("请先按 R 开始录音")
                        continue
                        
                    audio_file = recorder.stop_recording()
                    
                    if audio_file:
                        # 1. 语音转文本
                        user_query = await loop.run_in_executor(None, transcribe_audio, audio_file)
                        
                        if user_query:
                            # 2. 调用 DeepSeek (附带工具定义)
                            print(f"正在请求 DeepSeek (Query: {user_query})...")
                            client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
                            
                            try:
                                response = client.chat.completions.create(
                                    model="deepseek-chat",
                                    messages=[
                                        {"role": "system", "content": "You are a helpful assistant. Use the provided tools to answer user questions if needed."},
                                        {"role": "user", "content": user_query}
                                    ],
                                    tools=openai_tools,
                                    stream=False
                                )
                                
                                message = response.choices[0].message
                                
                                # 3. 检查是否有工具调用
                                if message.tool_calls:
                                    print(f"DeepSeek 请求调用工具: {len(message.tool_calls)} 个")
                                    
                                    for tool_call in message.tool_calls:
                                        func_name = tool_call.function.name
                                        func_args = json.loads(tool_call.function.arguments)
                                        
                                        print(f">>> 正在调用本地 MCP 工具: {func_name}({func_args})")
                                        
                                        # 4. 执行 MCP 工具
                                        result = await session.call_tool(func_name, arguments=func_args)
                                        
                                        # 打印结果
                                        for content in result.content:
                                            if content.type == "text":
                                                print(f"<<< 工具执行结果: {content.text}")
                                            else:
                                                print(f"<<< 工具执行结果(非文本): {content}")
                                else:
                                    print(f"DeepSeek 直接回复: {message.content}")
                                    
                            except Exception as e:
                                print(f"DeepSeek 请求失败: {e}")

                elif cmd == 'Q':
                    if recorder.is_recording:
                        recorder.stop_recording()
                    break
    
    recorder.close()

if __name__ == "__main__":
    # Windows 异步策略修复
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(run_agent())
    except ImportError:
        print("错误: 缺少必要库，请安装: pip install pyaudio openai-whisper openai mcp")
    except Exception as e:
        print(f"发生错误: {e}")
