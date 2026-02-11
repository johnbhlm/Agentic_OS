from abc import ABC, abstractmethod

class TTS(ABC):
    """
    文本转语音抽象接口。
    所有具体的 TTS 实现都应继承此类并实现 speak() 方法。
    """

    @abstractmethod
    def speak(self, text: str) -> None:
        """
        将给定文本转换为语音并播放。

        :param text: 待播报的文本
        """
        pass