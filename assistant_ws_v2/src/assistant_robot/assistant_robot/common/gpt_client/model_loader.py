import yaml
import os
import logging
from assistant_robot.common.gpt_client.factory import ProviderFactory

logger = logging.getLogger(__name__)

def load_llm_client(config_path: str):
    """
    从 YAML 配置文件加载 LLM 客户端。
    :param config_path: 配置文件路径（gpt_config.yaml）
    :return: 已实例化的 LLM 客户端
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"LLM config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        raise ValueError("Empty LLM config")

    logger.info(f"Loading LLM client from config: {config_path}")
    return ProviderFactory.create(config)
