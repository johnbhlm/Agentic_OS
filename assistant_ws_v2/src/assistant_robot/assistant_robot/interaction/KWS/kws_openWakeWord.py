import numpy as np
import logging
import resampy
import time
from collections import deque
from openwakeword.model import Model
from assistant_robot.interaction.KWS.kws_interface import BaseKWS

logger = logging.getLogger(__name__)

class OpenWakeWordKWS(BaseKWS):
    def __init__(self):
        """
        OpenWakeWord KWS 实现
        """
        # self.model_paths = model_paths
        # 定义多个唤醒词模型路径 maintenance
        self.model_paths = [
            "/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/assistant_robot/interaction/KWS/models/你好思灵_data10000_step20000_0.6_0.6_quick.onnx",
            "/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/assistant_robot/interaction/KWS/models/hey_agile_data10000_step20000_0.8_0.8.onnx"
        ]
        # self.model_paths = [
        #     "/home/diana/Code/assistant_ws_v2/src/assistant_robot/assistant_robot/interaction/KWS/models/你好思灵_data10000_step20000_0.6_0.6_quick.onnx",
        #     # "/home/diana/Code/assistant_ws_v2/src/assistant_robot/assistant_robot/interaction/KWS/models/hey_agile_data10000_step20000_0.8_0.8.onnx"
        # ]
        self.consecutive_frames = 2
        self.cooldown = 2.0 
        self.threshold = 0.5 #置信度阈值（官方推荐 0.5）
        self.score_window = deque(maxlen=self.consecutive_frames)
        self.last_trigger_time = 0

        # 1. 加载模型
        if self.model_paths is None or len(self.model_paths) == 0:
            logger.info("No model path provided, using default OpenWakeWord model.")
            self.model = Model()  # 默认加载预训练模型
        else:
            logger.info(f"Loading custom wakeword models: {self.model_paths}")
            self.model = Model(
                inference_framework="onnx",
                wakeword_models=self.model_paths,
                enable_speex_noise_suppression=True,
                )

        logger.info(f"OpenWakeWord KWS initialized with models: {list(self.model.models.keys())}")

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        检测唤醒词（带平滑+防抖）
        :param audio_chunk: np.ndarray PCM16, 16kHz 单声道
        :return: (bool, float) -> 是否触发, 最高分
        """
        
        predictions = self.model.predict(audio_chunk) # {keyword: score}
        best_keyword, best_score = max(predictions.items(), key=lambda x: x[1])
        # logger.info(f"KWS prediction: {predictions}")

        # 记录分数
        self.score_window.append(best_score)

        # 连续帧检测
        if all(s > self.threshold for s in self.score_window):
            now = time.time()
            if now - self.last_trigger_time > self.cooldown:
                self.last_trigger_time = now
                logger.info(f"Wakeword detected: {best_keyword} (score={best_score:.2f})")
                self.score_window.clear()
                return True, best_score

        return False, best_score

    # def reset(self):
    #     """
    #     清空缓存的分数
    #     """
    #     logger.info("KWS分数缓冲已清空")

