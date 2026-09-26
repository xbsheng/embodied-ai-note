import pyaudio
import wave

# 配置参数
CHUNK = 1024  # 缓冲区大小
FORMAT = pyaudio.paInt16  # 量化深度 16位
CHANNELS = 1  # 单声道
RATE = 16000  # 采样率 16k
RECORD_SECONDS = 5  # 录音时长(秒)
WAVE_OUTPUT_FILENAME = "output.wav"  # 输出文件名

def record_audio():
    p = pyaudio.PyAudio()

    print("开始录音...")

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("录音结束")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # 保存为 WAV 文件
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"音频已保存到 {WAVE_OUTPUT_FILENAME}")

if __name__ == "__main__":
    record_audio()
