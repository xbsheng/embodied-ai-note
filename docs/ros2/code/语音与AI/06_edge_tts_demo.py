import asyncio
import edge_tts
import sys

# 配置参数
TEXT = "你好，我是由微软 Edge TTS 生成的语音。我的声音更加自然，富有情感。"
VOICE = "zh-CN-XiaoxiaoNeural"  # 推荐使用的中文语音 (晓晓)
OUTPUT_FILE = "edge_tts_output.mp3"
RATE = "+0%"  # 语速调整，例如 "-10%", "+50%"
VOLUME = "+0%"  # 音量调整

async def main():
    print(f"正在使用语音: {VOICE}")
    print(f"正在生成音频到: {OUTPUT_FILE} ...")
    
    communicate = edge_tts.Communicate(TEXT, VOICE, rate=RATE, volume=VOLUME)
    
    await communicate.save(OUTPUT_FILE)
    
    print("生成完成！")
    print(f"请播放 {OUTPUT_FILE} 试听。")

def list_voices():
    """列出所有可用的中文语音"""
    async def _list():
        voices = await edge_tts.list_voices()
        print("\n--- 可用的中文语音列表 ---")
        for v in voices:
            if "zh-CN" in v["ShortName"]:
                print(f"- {v['ShortName']} ({v['Gender']})")
    
    # 针对 Windows 系统的事件循环策略设置
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(_list())

if __name__ == "__main__":
    # 针对 Windows 系统的事件循环策略设置，解决 "Event loop is closed" 错误
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 如果想查看可用语音列表，取消下面这行的注释
    # list_voices()
    
    try:
        asyncio.run(main())
    except ImportError:
        print("错误: 未找到 edge-tts 库")
        print("请运行: pip install edge-tts")
    except Exception as e:
        print(f"发生错误: {e}")
