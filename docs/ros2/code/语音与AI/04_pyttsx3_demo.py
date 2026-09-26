import pyttsx3

def demo_tts():
    # 初始化语音引擎
    engine = pyttsx3.init()

    # 1. 基础朗读
    print("1. 基础朗读测试...")
    text = "你好，这是一个基于 pyttsx3 的文本转语音测试。"
    engine.say(text)
    engine.runAndWait()

    # 2. 获取并设置属性 (语速、音量)
    print("\n2. 调整属性测试...")
    
    # 获取当前语速
    rate = engine.getProperty('rate')
    print(f"当前语速: {rate}")
    # 设置新语速 (默认通常是 200)
    engine.setProperty('rate', 150) 
    engine.say("我现在说话慢了一点。")
    
    # 获取当前音量
    volume = engine.getProperty('volume')
    print(f"当前音量: {volume}")
    # 设置音量 (范围 0.0 到 1.0)
    engine.setProperty('volume', 0.8)

    # 3. 更换语音 (声音)
    print("\n3. 更换语音测试...")
    voices = engine.getProperty('voices')
    print(f"检测到 {len(voices)} 个语音包")
    
    # 尝试切换不同的声音
    # 注意：不同系统安装的语音包不同，这里只演示切换逻辑
    for index, voice in enumerate(voices):
        print(f"语音 {index}: {voice.name}")
        # 只演示前两个，避免太长
        if index < 2:
            engine.setProperty('voice', voice.id)
            engine.say(f"我是语音包 {index}，你好。")
    
    # 恢复默认设置 (可选)
    # engine.setProperty('rate', rate)

    # 4. 保存音频到文件
    print("\n4. 保存音频文件测试...")
    save_text = "这段音频已经被保存到了文件中。"
    output_file = "tts_output.mp3"
    engine.save_to_file(save_text, output_file)
    print(f"正在保存到 {output_file}...")
    
    # 注意：save_to_file 后必须调用 runAndWait 才能真正写入
    engine.runAndWait()
    print("保存完成。")

if __name__ == "__main__":
    try:
        demo_tts()
    except ImportError:
        print("错误: 未找到 pyttsx3 库")
        print("请运行: pip install pyttsx3")
    except Exception as e:
        print(f"发生错误: {e}")
