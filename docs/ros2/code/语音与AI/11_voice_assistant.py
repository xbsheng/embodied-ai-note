import pyaudio
import wave
import threading
import time
import os
import whisper
import asyncio
import edge_tts
import sys
from openai import OpenAI

# ----------------- 配置参数 -----------------
# 录音配置
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
WAVE_OUTPUT_FILENAME = "input_voice.wav"

# Whisper 配置
WHISPER_MODEL_TYPE = "base"

# DeepSeek 配置
API_KEY = 'sk-a80719c8b9cc4c708195d7f84fdd4a70'
BASE_URL = "https://api.deepseek.com"

# TTS 配置
TTS_VOICE = "zh-CN-XiaoxiaoNeural"  # 默认使用标准女声，可改为河南话 "zh-CN-henan-YundengNeural"
TTS_OUTPUT_FILE = "response_voice.mp3"
TTS_RATE = "+0%"
TTS_VOLUME = "+100%"

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

# ----------------- 2. 语音识别模块 (Whisper) -----------------
def transcribe_audio(audio_file):
    if not os.path.exists(audio_file):
        print("错误: 找不到录音文件")
        return None

    print(f"正在加载 Whisper 模型 ('{WHISPER_MODEL_TYPE}')...")
    try:
        model = whisper.load_model(WHISPER_MODEL_TYPE)
        print(f"正在识别...")
        # fp16=False 避免 CPU 警告
        result = model.transcribe(audio_file, fp16=False)
        text = result["text"].strip()
        print(f"识别结果: {text}")
        return text
    except Exception as e:
        print(f"识别出错: {e}")
        return None

# ----------------- 3. 大模型对话模块 (DeepSeek) -----------------
def chat_with_llm(query):
    print("正在请求 DeepSeek...")
    try:
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Please answer in Chinese."},
                {"role": "user", "content": query},
            ],
            stream=False
        )
        answer = response.choices[0].message.content
        print(f"DeepSeek 回答:\n{answer}")
        return answer
    except Exception as e:
        print(f"LLM 请求出错: {e}")
        return None

# ----------------- 4. 语音合成模块 (Edge TTS) -----------------
async def text_to_speech(text):
    print(f"正在生成语音回复 ({TTS_VOICE})...")
    try:
        communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME)
        await communicate.save(TTS_OUTPUT_FILE)
        print(f"语音已生成: {TTS_OUTPUT_FILE}")
        
        # 自动播放 (Windows)
        if sys.platform.startswith('win'):
            print("开始播放回复...")
            os.startfile(TTS_OUTPUT_FILE)
    except Exception as e:
        print(f"TTS 生成出错: {e}")

# ----------------- 主程序 -----------------
def main():
    # Windows 异步策略修复
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    recorder = AudioRecorder()
    print("=== 智能语音助手 ===")
    print("流程: 录音(R) -> 停止(S) -> 识别 -> 思考 -> 播报")
    print("输入 'R' 开始录音，'Q' 退出")

    try:
        while True:
            cmd = input("\n请输入指令 (R/S/Q): ").strip().upper()
            
            if cmd == 'R':
                recorder.start_recording()
                
            elif cmd == 'S':
                if not recorder.is_recording:
                    print("请先按 R 开始录音")
                    continue
                    
                audio_file = recorder.stop_recording()
                
                if audio_file:
                    # 步骤 1: 语音转文本
                    user_text = transcribe_audio(audio_file)
                    
                    if user_text:
                        # 步骤 2: LLM 思考
                        ai_response = chat_with_llm(user_text)
                        
                        if ai_response:
                            # 步骤 3: 文本转语音
                            asyncio.run(text_to_speech(ai_response))
            
            elif cmd == 'Q':
                if recorder.is_recording:
                    recorder.stop_recording()
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        recorder.close()
        print("程序退出")

if __name__ == "__main__":
    main()
