import logging
from assistant_robot.common.gpt_client.openai_client import OpenAIClient
from assistant_robot.common.gpt_client.qwen_client import QwenClient
# from openai_client import OpenAIClient
# from qwen_client   import QwenClient

logger = logging.getLogger(__name__)

class ProviderFactory:
    """
    通用工厂类：根据配置文件中的 default_provider 创建对应的 LLM 客户端
    """
    _map = {
        "openai": OpenAIClient,
        "qwen":   QwenClient,
        # 可以在未来扩展更多模型，如 deepseek, gemini 等
    }

    @staticmethod
    def create(config: dict):
        """
        :param config: 整个 gpt_config.yaml 的内容（Dict）
        :return: 已实例化的 BaseLLMClient 子类
        """
        if not isinstance(config, dict):
            raise ValueError("Invalid config: expected dict")
        
        provider_name = config.get("default_provider")
        if not provider_name:
            raise ValueError("Missing 'default_provider' in config")
        if provider_name not in config["providers"]:
            raise ValueError(f"Provider '{provider_name}' not found in config")

        provider_cfg = config.get("providers", {}).get(provider_name)
        if not provider_cfg:
            raise ValueError(f"Provider config '{provider_name}' not found")

        client_cls = ProviderFactory._map.get(provider_name.lower())
        if not client_cls:
            raise ValueError(f"Unsupported provider: {provider_name}")

        # logger.info(f"Creating LLM client for provider: {provider_name}")
        # 把 provider 的配置信息和 templates 一起传入
        return client_cls(provider_cfg)
