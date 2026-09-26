import pyaudio
import wave
import threading
import time

# 配置参数
CHUNK = 1024  # 缓冲区大小
FORMAT = pyaudio.paInt16  # 量化深度 16位
CHANNELS = 1  # 单声道
RATE = 16000  # 采样率 16k
WAVE_OUTPUT_FILENAME = "output.wav"  # 输出文件名

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
        print("正在录音... (输入 S 并回车停止)")
        while self.is_recording:
            data = self.stream.read(CHUNK)
            self.frames.append(data)
        
        # 停止录音后的清理工作
        self.stream.stop_stream()
        self.stream.close()

    def start_recording(self):
        if self.is_recording:
            print("已经在录音中...")
            return

        self.frames = []  # 清空旧数据
        self.is_recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()
        print("开始录音进程已启动")

    def stop_recording(self):
        if not self.is_recording:
            print("当前未在录音")
            return

        print("正在停止录音...")
        self.is_recording = False
        if self.record_thread:
            self.record_thread.join()  # 等待录音线程结束
        
        self.save_file()

    def save_file(self):
        if not self.frames:
            print("没有录制到音频数据")
            return

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print(f"录音结束，音频已保存到 {WAVE_OUTPUT_FILENAME}")

    def close(self):
        self.p.terminate()

def main():
    recorder = AudioRecorder()
    print("音频录制控制脚本")
    print("输入 'R' (或 'r') 开始录音")
    print("输入 'S' (或 's') 停止录音并保存")
    print("输入 'Q' (或 'q') 退出程序")

    try:
        while True:
            cmd = input("请输入指令: ").strip().upper()
            if cmd == 'R':
                recorder.start_recording()
            elif cmd == 'S':
                recorder.stop_recording()
            elif cmd == 'Q':
                if recorder.is_recording:
                    recorder.stop_recording()
                break
            else:
                print("无效指令，请输入 R, S 或 Q")
    except KeyboardInterrupt:
        if recorder.is_recording:
            recorder.stop_recording()
    finally:
        recorder.close()
        print("程序已退出")

if __name__ == "__main__":
    main()
