import os
import logging
os.environ["DISABLE_TQDM"] = "1"
logging.getLogger().setLevel(logging.ERROR)

try:
    import tqdm
    tqdm.tqdm = lambda iterable=None, *args, **kwargs: iterable or []
except ImportError:
    pass

import contextlib
import sys
import torchaudio

from assistant_robot.interaction.ASR.transcriber_interface import Transcriber
# import funasr
from funasr import AutoModel

# logger = logging.getLogger(__name__)

class FunASRTranscriber(Transcriber):
    def __init__(
        self,
        model_name: str = "paraformer-zh",
        vad_model: str   = "fsmn-vad",
        punc_model: str  = "ct-punc",
        device: str      = "cpu",
        hotword: str     = None
    ):
        """
        :param model_name: ASR 模型名
        :param vad_model: VAD 模型名
        :param punc_model: 标点模型名
        :param device: 设备字符串，如 "cuda:0" 或 "cpu"
        :param hotword: 可选热词，用于增强识别
        """
        # self.hotword = "小爱同学:30, 好的:20, 是的:20, 谢谢:25"
        # self.hotword = "xiao ling tong xue:30, 小灵同学:30, 是的:20, 谢谢:25"
        self.hotword = "谢谢:30"
        # 初始化 FunASR 模型
        self.model = AutoModel(
            model=model_name,
            vad_model=vad_model,
            punc_model=punc_model,
            device=device,
            disable_update=True
        )

    def transcribe(self, wav_path: str) -> str:
        """
        对 wav_path 做 ASR 转写，返回纯文本结果。
        """
        # 调用 generate 接口
        # 如果设置了热词，传入 hotword 参数
        if self.hotword:
            results = self.model.generate(input=wav_path, hotword=self.hotword)
        else:
            results = self.model.generate(input=wav_path)
        # 返回第一条结果的 text 字段
        if isinstance(results, list) and results:
            return results[0].get("text", "").strip()
        return ""