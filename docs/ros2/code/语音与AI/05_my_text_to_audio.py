import pyttsx3

def setup_engine():
    engine = pyttsx3.init()
    
    # 1. 设置语速为 80
    engine.setProperty('rate', 80)
    
    # 2. 设置音量为最大 (1.0)
    engine.setProperty('volume', 1.0)
    
    # 3. 查找并设置中文语音
    voices = engine.getProperty('voices')
    chinese_voice_id = None
    
    print("正在查找中文语音包...")
    for voice in voices:
        # 尝试通过名称或ID识别中文语音 (适用于 Windows/Mac/Linux)
        # Windows 常见: "Huihui", "Yaoyao", "Chinese"
        if "chinese" in voice.name.lower() or "zh" in voice.id.lower() or "huihui" in voice.name.lower():
            chinese_voice_id = voice.id
            print(f"找到中文语音: {voice.name}")
            break
            
    if chinese_voice_id:
        engine.setProperty('voice', chinese_voice_id)
    else:
        print("警告: 未自动检测到中文语音包，将使用默认语音。")
        
    return engine

def speak(text):
    engine = setup_engine()
    print(f"正在朗读: {text}")
    engine.say(text)
    engine.runAndWait()

if __name__ == "__main__":
    test_text = "你好，这是一个中文语音测试。当前语速设置为80，音量已调至最大。"
    speak(test_text)
