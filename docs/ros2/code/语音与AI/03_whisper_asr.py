import whisper
import os

# 配置参数
AUDIO_FILE = "output.wav"
MODEL_TYPE = "large"  # 可选: tiny, base, small, medium, large

def transcribe_audio():
    # 检查文件是否存在
    if not os.path.exists(AUDIO_FILE):
        print(f"错误: 找不到文件 {AUDIO_FILE}")
        print("请先运行 01_audio_record.py 或 02_record_ctrl.py 生成录音文件。")
        return

    print(f"正在加载 Whisper 模型 ('{MODEL_TYPE}')...")
    try:
        model = whisper.load_model(MODEL_TYPE)
    except Exception as e:
        print(f"加载模型失败: {e}")
        print("请确保已安装 openai-whisper: pip install openai-whisper")
        print("并且系统已安装 ffmpeg")
        return

    print(f"正在识别 {AUDIO_FILE} ...")
    try:
        # result = model.transcribe(AUDIO_FILE) 
        # fp16=False 避免在 CPU 运行时出现警告
        result = model.transcribe(AUDIO_FILE, fp16=False)
        
        text = result["text"]
        
        print("\n识别结果:")
        print("-" * 30)
        print(text.strip())
        print("-" * 30)
        
    except Exception as e:
        print(f"识别过程中出错: {e}")

if __name__ == "__main__":
    transcribe_audio()
