from abc import ABC, abstractmethod

class Transcriber(ABC):
    """
    抽象转写接口，定义所有 ASR 转写器需实现的方法。
    具体的转写器（如 OpenAITranscriber、LocalWhisperTranscriber、FunASRTranscriber）
    都应继承此类并实现 transcribe() 方法，以便在系统各处可无缝替换。
    """

    @abstractmethod
    def transcribe(self, wav_path: str) -> str:
        """
        对给定的 WAV 文件进行转写，返回识别出的文本。

        :param wav_path: 本地 WAV 文件完整路径
        :return: 识别后的文本字符串
        """
        raise NotImplementedError("Transcribe method must be implemented by subclasses")