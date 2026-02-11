import pyaudio, wave, threading, time, re, os
import sounddevice as sd
import webrtcvad
from queue import Queue
from datetime import datetime, timedelta
from pypinyin import pinyin, Style
import sys
import subprocess
import logging
import numpy as np
from threading import Lock,Event
from assistant_robot.common.utils import convert_to_pinyin

logger = logging.getLogger(__name__)

# =======================
# 状态定义
# =======================
STATE_IDLE = "IDLE"            # 未唤醒状态
STATE_WAKE_DETECTED = "WAKE"   # 唤醒词检测
STATE_LISTENING = "LISTENING"  # 正在录制指令
STATE_PROCESSING = "PROCESSING" # 指令处理中
STATE_SPEAKING = "SPEAKING"    # TTS 播报中


class SessionContext:
    """会话上下文管理"""
    def __init__(self, timeout=30.0):
        self.session_id = None
        self.start_time = None
        self.last_interaction = None
        self.timeout = timeout

    def start(self):
        self.session_id = f"session_{int(time.time()*1000)}"
        self.start_time = time.time()
        self.last_interaction = self.start_time
        logger.info(f"Session started: {self.session_id}")

    def update(self):
        self.last_interaction = time.time()

    def expired(self):
        return self.last_interaction and (time.time() - self.last_interaction > self.timeout)

    def reset(self):
        logger.info(f"Session reset: {self.session_id}")
        self.session_id = None
        self.start_time = None
        self.last_interaction = None

class SpeechManager:
    def __init__(self,transcriber,tts,
                 kws: str = "ni hao si ling", #xiao ai tong xue
                 rate: int = 16000,
                 vad_mode: int = 3,
                 chunk: int = 1024,
                 session_timeout: float = 180.0,
                 min_record_time: float = 0.5,
                 no_speech_threshold: float = 1.5,
                 max_command_duration: float = 10.0,):
        """
        :param kws: 唤醒词（拼音形式）
        :param rate: 采样率
        :param vad_mode: webrtcvad 敏感度 0-3
        :param chunk: 每次读取帧数
        """
        self.transcriber = transcriber 
        self.tts = tts
        # self._confirm = confirm_fn
        self.kws = kws

        # audio settings
        self.rate = rate
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.CHUNK = chunk
        self.AUDIO_FILE = "temp.wav"  # ASR 临时文件
        self.AUDIO_Denoise_FILE = "temp_denoise.wav"  # ASR 临时文件

        # timing thresholds
        # self.waited_kws_time = waited_kws_time # 唤醒后等待命令的最大时长
        self.MIN_RECORD_TIME = min_record_time # 最小录音时长，秒
        self.NO_SPEECH_THRESHOLD = no_speech_threshold # 静音后停止录制，秒
        self.MAX_COMMAND_DURATION = max_command_duration

        # session and state
        # 状态与会话
        self.state = STATE_IDLE
        self.session = SessionContext(timeout=session_timeout)
        self.state_lock = Lock()
        self.wake_event = Event()

        # TTS / interruption
        self.is_speaking = False       # TTS 播报
        self.interrupt = False         # 用户插话打断标志

        # vad
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(vad_mode)
        self.audio_queue = Queue()

        # 抑制逻辑
        # self.suppress_until = 0.0     # 抑制检测的截止时间
        # self.kws_threshold = 0.8     # 调高唤醒阈值，减少误触发
        # self.suppress_reset_sec = 5.0
        # self.suppress_tts_sec = 3.0

        self.transcribe_callback = None         
        
    def set_state(self, new_state):
        with self.state_lock:
            logger.info(f"State changed: {self.state} -> {new_state}")
            self.state = new_state

    def get_state(self):
        with self.state_lock:
            return self.state
        
    def set_transcription_callback(self, callback):
        self.transcribe_callback = callback

    # =======================
    # 音频与ASR
    # =======================
    def _is_valid_audio_input(self, audio_input, threshold: float = 500):
        """
        判断音频是否为有效语音，支持原始 bytes 或 list[bytes] 输入。
        """
        if not audio_input:
            return False

        if isinstance(audio_input, list):
            audio_bytes = b''.join(audio_input)
        elif isinstance(audio_input, bytes):
            audio_bytes = audio_input
        else:
            logger.error("无效的音频输入类型")
            return False

        pcm_data = np.frombuffer(audio_bytes, dtype=np.int16)
        return np.max(np.abs(pcm_data)) > threshold

    def _check_vad_activity(self, audio_data):
        num, rate = 0, 0.4
        step = int(self.rate * 0.02)
        flag_rate = round(rate * len(audio_data) // step)

        for i in range(0, len(audio_data), step):
            chunk = audio_data[i:i + step]
            if len(chunk) == step and self.vad.is_speech(chunk, sample_rate=self.rate):
                num += 1

        return num > flag_rate
    
    # =======================
    # 唤醒 & 会话管理
    # =======================
    def _asr_wake_up(self, text: str) -> bool:
        """
        处理唤醒词检测并唤醒
        """
        pinyin_text = convert_to_pinyin(text)
        if self.kws in pinyin_text:                
            logger.info("wake_up: key works detected and wake up sucess")
            return True
        logger.info("wake_up: key works detect fail,wake up fail")
        return False

    def _wake_up(self):
        """
        触发唤醒流程
        """
        self._speak("在呢，请讲。")
        self.session.start()
        self.set_state(STATE_LISTENING)
        logger.info("wake_up: key works detected and wake up sucess")
    # =======================
    # 会话过期检查
    # =======================
    def _check_session_expired(self):
        if self.session.expired():
            self._speak("您太久没有说话了，我先退下了，如需帮助请再次唤醒我。")
            self.session.reset()
            self.set_state(STATE_IDLE)
    
    def reset(self):
        self.session.reset()
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()# 清空队列，防止残留音频触发
        self.set_state(STATE_IDLE)
        # self.suppress_until = time.time() + self.suppress_reset_sec  # reset 后抑制
        # logger.info(f"Reset: 回到 WAKE 模式 ({self.suppress_reset_sec} s 抑制)")

    # =======================
    # TTS
    # =======================
    def _speak(self, text: str):
        def _run():
            # self.suppress_until = time.time() + self.suppress_tts_sec  # 播放期间+3秒抑制
            #按播报文本长度动态调整抑制时长，确保整个 TTS 播放过程都被覆盖。
            # self.suppress_until = time.time() + max(self.suppress_tts_sec, len(text) * 0.5)

            self.is_speaking = True
            try:
                self.tts.speak(text)
            finally:
                self.is_speaking = False
        threading.Thread(target=_run, daemon=True).start()
    
    # =======================
    # 指令监听
    # =======================
    def _listen_command(self):
        """
        唤醒后，基于 VAD 录制用户命令，静音或最长超时后停止
        """
        # self.set_state(STATE_LISTENING)

        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT,channels=self.CHANNELS,rate=self.rate,input=True,frames_per_buffer=self.CHUNK)

        segments = []
        last_active = time.time()
        start_time = time.time()
        logger.info("Recording command...")

        while True:
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            if self._check_vad_activity(data):
                segments.append(data)
                last_active = time.time()
            # 超时或检测到静音超过门槛即结束录制
            if time.time() - last_active > self.NO_SPEECH_THRESHOLD or time.time() - start_time > self.MAX_COMMAND_DURATION:
                logger.info("超时或检测到静音超时,结束录制")
                break
        stream.stop_stream()
        stream.close()
        p.terminate()

        if not segments or not self._is_valid_audio_input(segments):
            logger.info("无效的指令音频，，继续监听")
            # self.reset()
            return

        # save to WAV file 
        with wave.open(self.AUDIO_FILE, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(p.get_sample_size(self.FORMAT))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(segments))
        
        # #*************  start denoise ******************
        # env = os.environ.copy()
        # env["LD_LIBRARY_PATH"] = "/home/maintenance/Code/assistant_ws/src/assistant_robot_v2/assistant_robot/interaction/ASR/Denoise/2025.7.18/WavNoiseReduction-linux-x86_64/WavNoiseReduction/lib:" + env.get("LD_LIBRARY_PATH", "")
        
        # result = subprocess.run(
        #     ["/home/maintenance/Code/assistant_ws/src/assistant_robot_v2/assistant_robot/interaction/ASR/Denoise/2025.7.18/WavNoiseReduction-linux-x86_64/WavNoiseReduction/WavNoiseReduction",
        #      "/home/maintenance/Code/assistant_ws/src/assistant_robot_v2/assistant_robot/temp.wav",
        #      "/home/maintenance/Code/assistant_ws/src/assistant_robot_v2/assistant_robot/temp_denoise.wav"],
        #     env=env
        # )
        
        
        # self.set_state(STATE_PROCESSING)

        # ASR 转写命令
        try:
            text = self.transcriber.transcribe(self.AUDIO_FILE)
            logger.info(f"🧾 [ASR] 识别结果: {text}")
            print(f"🧾 [ASR] 识别结果: {text}")
        except Exception as e:
            logger.info(" ASR 失败")
            logger.error("ASR error: %s", e, exc_info=True)
            # self.reset()
            return

        # filter
        # if len(text) < 2 or re.fullmatch(r"[啊嗯哦唉]*", text):
        if len(text) < 2 or re.fullmatch(r"^(嗯|啊|哦|唉|呃|啊哈|唔|嗯嗯|呃呃|哎呀|对呀|是啊|是呀)$", text):
            logger.info("指令过短或无效")
            # self.reset()
            return
    
        logger.info(f"ASR 识别成功，用户指令: {text}")

        # self.session.update()
        
        # 把文本交给上层回调
        if self.transcribe_callback:
            self.transcribe_callback(text)

    # =======================
    # 主循环
    # =======================
    def _record_audio_loop(self):        
        logger.info("👂 开始唤醒词监听...") 
        while True:
            current_state = self.get_state()

            # 会话过期检查
            if current_state in [STATE_LISTENING, STATE_PROCESSING]:
                if self.session.expired():
                    self._speak("本次对话已超时，将结束对话，如需帮助请再次唤醒我。")
                    self.reset()
                    continue

            # 空闲状态 -> 等待唤醒
            if current_state == STATE_IDLE:
                sys.stdout.write("🚨 等待唤醒...\r")
                sys.stdout.flush()
                if self.wake_event.wait(timeout=0.1):
                    self.wake_event.clear()
                    self._wake_up()
                continue

            # 指令监听
            elif current_state == STATE_LISTENING:
                sys.stdout.write("🎙️ 已唤醒，监听指令中...\r")
                sys.stdout.flush()
                self._listen_command()
                # self.reset()
                continue

            time.sleep(0.05) # 避免 CPU 占用过高
  
            
    def start(self):
        thread = threading.Thread(target=self._record_audio_loop,daemon = True)
        thread.start()

    