"把通用逻辑（重试、限流、日志、Prompt 渲染）都放到一个父类里，只留抽象的“发请求”接口给子类去实现。"

import time
import logging
from abc import ABC, abstractmethod
import backoff

# from prompt_manager import PromptManager
# 尝试导入 PromptManager；若路径未配置，使用空实现避免执行错误
try:
    from assistant_robot.common.gpt_client.prompt_manager import PromptManager
except ImportError:
    class PromptManager:
        def __init__(self, cfg): pass
        def render(self, key, **kwargs): return ""

class BaseLLMClient(ABC):
    """
    抽象基类，封装对不同大模型供应商的通用调用流程：
    - Prompt 渲染
    - 重试逻辑
    - 请求构建与发送
    - 响应解析
    """

    def __init__(self, config: dict):
        """
        :param config: GPT 客户端的完整配置字典，
                       包含 "api"、"templates"、"templates_path" 等字段
        """
        api_cfg = config["api"]
        self.cfg = api_cfg
        self.timeout = api_cfg.get("timeout", 30)
        self.max_retries = api_cfg.get("max_retries", 3)
        self.logger = logging.getLogger(self.__class__.__name__)

        # 初始化 PromptManager，用于渲染各模块模板
        self.prompt_mgr = PromptManager({
            "templates": config.get("templates", {}),
            "templates_path": config.get("templates_path", "")
        })

    @backoff.on_exception(backoff.expo,
                          Exception,
                          max_tries=lambda self: self.max_retries,
                          jitter=backoff.full_jitter)
    def _request_with_retry(self, payload: dict) -> dict:
        """
        带重试的请求封装，交由子类实现 _raw_request 来发送
        """
        return self._raw_request(payload)

    def chat(self, template_key: str, **kwargs) -> str:
        """
        通用接口：根据模板 key + 参数渲染 prompt，
        构建 payload，发送请求并解析返回内容。
        """
        # 1. 渲染 Prompt
        prompt = self._render_prompt(template_key, **kwargs)
        # 2. 构建请求体
        payload = self._build_payload(prompt, **kwargs)
        # 3. 发送请求
        start = time.time()
        resp = self._request_with_retry(payload)
        elapsed = time.time() - start
        self.logger.info(f"[{self.__class__.__name__}] {template_key} took {elapsed:.2f}s")
        # 4. 解析响应
        return self._parse_response(resp)

    def _render_prompt(self, template_key: str, **kwargs) -> str:
        """
        使用 PromptManager 渲染指定模板
        """
        return self.prompt_mgr.render(template_key, **kwargs)

    @abstractmethod
    def _build_payload(self, prompt: str, **kwargs) -> dict:
        """
        构建模型供应商所需的请求体，
        payload 结构因供应商/模型而异，由子类实现
        """
        raise NotImplementedError

    @abstractmethod
    def _raw_request(self, payload: dict) -> dict:
        """
        执行真实的 HTTP/gRPC 调用，将 payload 发送给模型 API，
        由子类实现并返回原始响应字典
        """
        raise NotImplementedError

    def _parse_response(self, resp: dict) -> str:
        """
        通用的响应解析逻辑，默认适用于 ChatCompletion 类型接口
        若子类的返回格式不同，可覆写该方法
        """
        try:
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"Failed to parse response: {e}")
            raise

