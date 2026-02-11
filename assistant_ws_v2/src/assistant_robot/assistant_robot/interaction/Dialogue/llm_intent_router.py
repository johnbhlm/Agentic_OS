import logging
import yaml
from typing import Any, Dict, List

logger = logging.getLogger(__name__)
class LLMIntentRouter:
    """
    动态支持多意图分类。意图列表从配置文件读取，使用统一的 intent_classifier 模板让 LLM 返回具体意图名。
    """
    def __init__(self, gpt_client):
        """
        :param gpt_client: 统一的 GPT 客户端
        :param intent_config_path: 配置文件路径，如 "config/intent_config.yaml"
        """
        self.llm = gpt_client 
        self.intent_config_path = "/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/config/intent_config.yaml"
        # self.intent_config_path = "/home/diana/Code/assistant_ws_v2/src/assistant_robot/config/intent_config.yaml"

        # 1. 加载所有支持的意图
        with open(self.intent_config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        self.intents: List[Dict[str, Any]] = cfg.get("intents", [])
        if not self.intents:
            raise ValueError("No intents defined in intent_config.yaml")

    def classify(self, nl_instruction: str, context: str = None) -> str:
        """
        调用 LLM 进行意图分类，返回 intents 中的某个 name。
        """
        # 2. 准备调用所需的上下文,把 intents 列表传给模板
        # resp = self.llm.chat(
        #     template_key="llm_intent",
        #     utterance=nl_instruction,
        #     intents=self.intents
        # ).strip()
        resp = self.llm.chat(
            template_key="llm_intent",
            user_instruction=nl_instruction,
            context=context or ""
        ).strip()
    
        logger.info("Intent classification raw response: %s", resp)

        # 3. 尝试标准化输出：大写、去空格
        intent = resp.upper().strip()
        # 4. 校验是否在支持列表里
        names = [i["name"].upper() for i in self.intents]
        if intent not in names:
            logger.warning("LLM 返回未知意图 '%s'，默认路由到 UNKNOWN", intent)
            return "UNKNOWN"
        
        return intent
