import torch

import logging
logging.getLogger("TTS").setLevel(logging.ERROR)
import collections
from TTS.utils.radam import RAdam
#torch.serialization.add_safe_globals([RAdam, collections.defaultdict, dict])
from assistant_robot.interaction.TTS.tts_interface import TTS
from TTS.api import TTS as CoquiTTS_API
import sounddevice as sd
import re
import os
import contextlib
from TTS.utils.manage import ModelManager
from queue import Queue
from threading import Thread

# 1) 匹配开头“第N步：”前缀
_step_re   = re.compile(r'^(第\d+步：)\s*')
# 2) 匹配后面直接跟“数字+任意标点+空格”
_prefix_re = re.compile(r'^\s*\d+[^\w\s]*\s*')

class CoquiTTS(TTS):
    def __init__(self, model_name="tts_models/zh-CN/baker/tacotron2-DDC-GST"):
        self.use_gpu = torch.cuda.is_available()
        print(f"[TTS-Coqui] using GPU: {self.use_gpu}")
        self.tts_zh = CoquiTTS_API("tts_models/zh-CN/baker/tacotron2-DDC-GST",progress_bar=False, gpu=self.use_gpu)  # 中文专用模型              
        self.tts_en = CoquiTTS_API("tts_models/en/ljspeech/vits", progress_bar=False,gpu=self.use_gpu) #单说话人.自带默认说话人

        self.sample_rate = 22050
        self._chinese_re = re.compile(r'[\u4e00-\u9fa5]')

         # 播放队列和后台线程
        self._play_queue = Queue()
        self._play_thread = Thread(target=self._playback_worker, daemon=True)
        self._play_thread.start()
    
    def _playback_worker(self):
        """后台线程，从队列取出 wav 并按顺序播放（阻塞式）"""
        while True:
            wav = self._play_queue.get()
            if wav is None:
                break
            sd.play(wav, samplerate=self.sample_rate)
            sd.wait()
    
    def _normalize(self, text: str) -> list[str]:
        """
        将文本按中英文逗号和中英文句号分句，
        保留分隔符，并保证每句都以中英文标点（, . ? ! ， 。 ？ ！）结尾。
        """
        # 1. 统一空白字符
        text = text.strip()

        raw_sentences = re.split(r'(?<=[。？！?.!])\s*', text) # 正则切分，保留中英文标点为句尾
        clean_sentences = []
        for sentence in raw_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            # 剔除仅有标点的句子
            if re.match(r'^[。？！?.!,，、\s]*$', sentence):
                continue
            # 补句号（中英文都可以）
            if not re.search(r'[。？！?.!]$', sentence):
                sentence += "。"
            clean_sentences.append(sentence)

        return clean_sentences
    
    def speak(self, text: str):
        """
        逐句调用 CoquiTTS 播报，每句前后补全与分割。
        """
        m = _step_re.match(text)
        header = ""
        if m:
            header = m.group(1)
            text   = text[m.end():]  # 去掉“第N步：”部分
        
        text = _prefix_re.sub("", text) # —— 再去除“1.” 或 “2、” 这类数字标号 —— #        
        text = header + text # —— 重组回“第N步：” + 实际内容 —— #
        
        sentences = self._normalize(text)
        # total = len(sentences)
        for sent in sentences:            
            # 如果含中文，就用中文模型
            if self._chinese_re.search(sent):
                engine = self.tts_zh
                args = {}
                print(f"🔊 [TTS-Coqui] 中文播报: {sent}")
            else:
                print(f"🔊 [TTS-Coqui] 英文播报: {sent}")
                engine, args= self.tts_en, {}

            with open(os.devnull, 'w') as fnull, \
                contextlib.redirect_stdout(fnull), \
                contextlib.redirect_stderr(fnull):
                wav = engine.tts(sent, **args)                
                # wav = self.tts.tts(sent,speaker=self.default_speaker,language=lang)
            # sd.play(wav, samplerate=self.sample_rate)
            # sd.wait()

            # 推到播放队列，立即返回，不阻塞
            self._play_queue.put(wav)
    
    def shutdown(self):
        """关闭播放线程"""
        self._play_queue.put(None)
        self._play_thread.join()
