import re
import numpy as np
import soundfile as sf
import torch
from kokoro import KModel, KPipeline
from pathlib import Path
import time
import sounddevice as sd
from queue import Queue
from threading import Thread
import cn2an
import inflect

import logging
logging.getLogger("TTS").setLevel(logging.ERROR)
from assistant_robot.interaction.TTS.tts_interface import TTS

class KokoroTTS(TTS):
    def __init__(self):
        # ---------------------
        # 配置
        # ---------------------
        self.SAMPLE_RATE = 24000
        DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

        ZH_REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
        EN_REPO = 'hexgrad/Kokoro-82M' 
        self.VOICE_ZH = 'zf_001'
        self.VOICE_EN = 'af_heart'
        N_ZEROS = 3000  # 静音过渡
        # 根据标点插入不同静音长度（单位是采样点，sample_rate=24000）
        self.PAUSE_LONG = int(0.5 * self.SAMPLE_RATE)   # 句号、问号、感叹号
        self.PAUSE_SHORT = int(0.25 * self.SAMPLE_RATE) # 逗号、顿号、分号

        # ---------------------
        # 初始化中英文模型
        # ---------------------
        self.model_zh = KModel(repo_id=ZH_REPO).to(DEVICE).eval()
        self.zh_pipeline = KPipeline(lang_code='z', repo_id=ZH_REPO, model=self.model_zh)

        self.model_en = KModel(repo_id=EN_REPO).to(DEVICE).eval()
        self.en_pipeline = KPipeline(lang_code='a', repo_id=EN_REPO, model=self.model_en)

        self._play_queue = Queue()
        self._play_thread = Thread(target=self._playback_worker, daemon=True)
        self._play_thread.start()
    
    def _playback_worker(self):
        """后台线程，从队列取出 wav 并按顺序播放（阻塞式）"""
        while True:
            wav = self._play_queue.get()
            if wav is None:
                break
            sd.play(wav, samplerate=self.SAMPLE_RATE)
            sd.wait()

    def _normalize_numbers(self, lang, text):
        """数字预处理：中文转中文数字，英文转英文读法"""
        if lang == 'zh':
            def replace_num(match):
                num_str = match.group()
                try:
                    return cn2an.an2cn(num_str, "smart")
                except Exception:
                    return num_str
            return re.sub(r'\d+(\.\d+)?', replace_num, text)

        elif lang == 'en':
            p = inflect.engine()
            def replace_num(match):
                num_str = match.group()
                try:
                    # 转成英文读法，去掉 and（避免 too British）
                    return p.number_to_words(num_str, andword="")
                except Exception:
                    return num_str
            return re.sub(r'\d+(\.\d+)?', replace_num, text)

        return text



    def _split_text_mixed(self,text):
        """
        按中文和英文分段，标点归中文（或英文）不单独拆出。
        """
        # pattern = re.compile(r'[\u4e00-\u9fff]+|[a-zA-Z0-9\s]+|[，。！？,.!?]')  # 先拆中英文主体（去除标点）
        pattern = re.compile(r'[\u4e00-\u9fff0-9]+|[a-zA-Z]+|[，。！？；、,.!?]')

        result = []
        buffer = ''
        current_lang = None

        for m in pattern.finditer(text):
            seg = m.group(0)
            if re.match(r'[，。！？,.!?]', seg):  # 标点
                # 标点加到缓冲里
                buffer += seg
            else:
                lang = 'zh' if re.search(r'[\u4e00-\u9fff]', seg) else 'en'
                # 如果切换语言，先存缓冲
                if current_lang is not None and lang != current_lang and buffer:
                    result.append((current_lang, buffer))
                    buffer = seg
                    current_lang = lang
                else:
                    buffer += seg
                    current_lang = lang
        if buffer:
            result.append((current_lang, buffer))
        return result

    # ---------------------
    # 语音合成
    # ---------------------
    def _synthesize(self,lang, text):
        if not text.strip():
            return np.array([], dtype=np.float32)
        if lang == 'zh':
            generator = self.zh_pipeline(text, voice=self.VOICE_ZH)
        else:
            generator = self.en_pipeline(text, voice=self.VOICE_EN)

        try:
            return next(generator).audio
        except StopIteration:
            print(f"警告: 语音生成空，跳过段落: {text}")
            return np.array([], dtype=np.float32)

    def _get_pause_duration(self,text_segment):
        """
        判断文本末尾标点符号类型，返回对应静音长度采样点数
        """
        if not text_segment:
            return 0
        last_char = text_segment[-1]
        if last_char in ['。', '！', '？','：', '.', '!', '?',':']:
            return self.PAUSE_LONG
        elif last_char in ['，', '、','；', ',', '，',';']:
            return self.PAUSE_SHORT
        else:
            return 0 
        
    # ---------------------
    # 主合成函数
    # ---------------------
    def _tts_mixed(self,text):
        parts = self._split_text_mixed(text)
        wavs = []
        for i, (lang, segment) in enumerate(parts):
            # print(f"合成第{i+1}段，语言={lang}，内容：{segment}")
            segment = self._normalize_numbers(lang, segment)
            audio = self._synthesize(lang, segment)
            pause_len = self._get_pause_duration(segment)
            if i > 0 and pause_len > 0:
                audio = np.concatenate([np.zeros(pause_len), audio])
            wavs.append(audio)
        
        print(f"🔊 [TTS] 播报: {text}")
        return np.concatenate(wavs) if wavs else np.array([], dtype=np.float32)
    
    def speak(self,text):
        wav = self._tts_mixed(text)
        if wav.size > 0:
            self._play_queue.put(wav)
        # sd.play(wav, samplerate=self.SAMPLE_RATE)
        # sd.wait()
