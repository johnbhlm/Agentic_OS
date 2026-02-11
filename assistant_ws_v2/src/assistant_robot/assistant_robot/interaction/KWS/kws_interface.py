from abc import ABC, abstractmethod
import numpy as np

class BaseKWS(ABC):
    """
    KWS (Keyword Spotting) 接口基类
    所有 KWS 引擎都必须继承并实现 detect 方法
    """
    
    @abstractmethod
    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        检测是否有唤醒词触发
        :param audio_chunk: float32 格式的音频帧（单声道，16kHz）
        :return: bool，True 表示检测到唤醒词
        """
        pass

    # @abstractmethod
    # def reset(self):
    #     """
    #     重置检测状态（如果模型内部有缓存机制）
    #     """
    #     pass
