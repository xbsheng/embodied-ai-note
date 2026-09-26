import asyncio
import edge_tts
import sys
import os

# 配置参数
TEXT = "弄啥嘞？我是河南话语音助手。今儿个天气不错，咱们去喝碗胡辣汤中不中？"
HENAN_VOICE = "zh-CN-shaanxi-XiaoniNeural"  # 河南话语音包
FALLBACK_VOICE = "zh-CN-XiaoxiaoNeural"    # 备用标准普通话
OUTPUT_FILE = "henan_output.mp3"
RATE = "+0%"   # 语速
VOLUME = "+100%" # 音量调节到最大

async def generate_audio(voice, text, output_file):
    print(f"正在尝试使用语音: {voice}")
    communicate = edge_tts.Communicate(text, voice, rate=RATE, volume=VOLUME)
    await communicate.save(output_file)

async def main():
    print(f"音量设置: {VOLUME}")
    
    try:
        await generate_audio(HENAN_VOICE, TEXT, OUTPUT_FILE)
        print("河南话语音生成成功！")
    except edge_tts.exceptions.NoAudioReceived:
        print(f"错误: 无法获取河南话语音 ({HENAN_VOICE})。")
        print("可能该语音包暂时不可用或受限。")
        print(f"正在切换到标准普通话 ({FALLBACK_VOICE})...")
        try:
            await generate_audio(FALLBACK_VOICE, TEXT, OUTPUT_FILE)
            print("标准普通话语音生成成功！")
        except Exception as e:
            print(f"生成失败: {e}")
            return
    except Exception as e:
        print(f"发生未知错误: {e}")
        return
    
    print(f"请播放 {OUTPUT_FILE} 试听。")
    
    # 尝试自动播放 (仅限 Windows)
    if sys.platform.startswith('win'):
        if os.path.exists(OUTPUT_FILE):
            print("尝试播放音频...")
            os.startfile(OUTPUT_FILE)

if __name__ == "__main__":
    # 针对 Windows 系统的事件循环策略设置
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except ImportError:
        print("错误: 未找到 edge-tts 库")
        print("请运行: pip install edge-tts")
    except Exception as e:
        print(f"发生错误: {e}")
