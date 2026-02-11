import os
import wave
import pyaudio
import time
import wave
import tempfile
import re
import logging

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 3
WAVE_OUTPUT = "command.wav"
CONFIRM_OUTPUT = "confirm.wav"

# 临时保存的确认录音文件
CONFIRM_WAV = "confirm.wav"

logger = logging.getLogger(__name__)

def get_confirmation(transcriber, record_seconds: int = RECORD_SECONDS) -> str:
    """
    录制 record_seconds 秒的音频到 CONFIRM_WAV，
    然后调用 transcriber.transcribe 文件来获取文本结果。

    :param transcriber: 实现 Transcriber 接口的实例
    :param record_seconds: 录音时长（秒）
    :return: 转写文本（小写、去除首尾空格）
    """
    # 1. 打开麦克风进行录音
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    frames = []
    for _ in range(int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    # 2. 停止流和 PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()

    # 3. 保存到 WAV 文件
    with wave.open(CONFIRM_WAV, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))

    # 4. 调用注入的 Transcriber 转写
    try:
        # with open(os.devnull, 'w') as fnull, redirect_stdout(fnull), redirect_stderr(fnull):
        text = transcriber.transcribe(CONFIRM_WAV) or ""
    except Exception as e:
        logger.error("confirm ASR failed: %s", e, exc_info=True)
        text = ""

    # 5. 返回小写、去首尾空格的结果
    return text.lower()#.strip()

def is_confirm(input: str) -> bool:
    # 结束对话的简单触发词
    END_TOKENS = {"", "拜拜", "结束", "谢谢", "thank you", "bye"}
    
    return any(tok in input.strip().lower() for tok in END_TOKENS)

def confirm_fn(tts,transcriber,prompt) -> bool:
    """
    :param prompt: TTS 提示语
    :return: True 表示“是”，False 表示“否”或超时
    """
    prompt = "请回答是或不。"
    tts.speak(prompt)
    resp = get_confirmation(transcriber,record_seconds=3)
    print(f"[确认] 识别到: {resp}")
    
    return bool(resp and ("正确" in resp or "是" in resp or resp.lower().startswith("y")))


def confirm_fn_(tts, transcriber, 
               prompt: str = "请回答 正确 或 错误。",
               record_seconds: float = 3.0,
               max_retries: int = 2,
               timeout: float = 5.0) -> bool:
    """
    TTS 提示 + ASR 录音确认。默认提示“请回答 正确 或 错误。”
    :param tts:        TTS 对象，需有 speak(text) 方法
    :param transcriber:ASR 对象，需有 transcribe(wav_path) -> str 方法
    :param prompt:     要播报的确认提示
    :param record_seconds: 每次录音时长（秒）
    :param retries:    最多重试次数
    :param timeout:    等待 ASR 返回的最大时长
    :return: True 表示确认（是/正确/yes），False 表示否定或最终超时
    """

    affirm_re = [
        re.compile(r"\b(是|正确|对|yes|y)\b", re.I),
    ]
    deny_re = [
        re.compile(r"\b(否|错误|取消|不|no|n)\b", re.I),
    ]
    prompt = "请回答正确或错误。",
    logger.info(f"confirm fun prompt: {prompt}")
    # pa = pyaudio.PyAudio()
    for attempt in range(max_retries):
        
        tts.speak(prompt) # 播报提示
        
        time.sleep(0.1) # 等待 TTS 启动
        resp = get_confirmation(transcriber, record_seconds)
        logger.info(f"[confirm_fn] attempt {attempt}/{max_retries}, ASR response: '{resp}'")
        
        if affirm_re.search(resp):
            return True
        if deny_re.search(resp):
            return False
        
        # 未匹配到，再次提示
        if attempt < max_retries:
            retry_prompt = {
                "zh": "没听清，请回答“是”或“否”。",
                "en": "Sorry, I didn’t catch that. Please say yes or no."
            }
            # 根据 prompt 语言简单判断
            if re.search(r"[^\x00-\x7F]+", prompt):
                tts.speak(retry_prompt["zh"])
            else:
                tts.speak(retry_prompt["en"])

    # 重试结束，返回 False
    logger.warning("confirm_fn: all retries exhausted, defaulting to False")
    return False
