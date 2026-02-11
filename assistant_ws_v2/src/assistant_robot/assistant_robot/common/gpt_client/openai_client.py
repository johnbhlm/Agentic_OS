import os
import requests
import logging

try:
    from assistant_robot.common.gpt_client.base_client import BaseLLMClient
except ImportError:
    # 为了兼容演示环境，如果导入失败，定义一个简单的替代基类
    from abc import ABC, abstractmethod
    class BaseLLMClient(ABC):
        def __init__(self, config): pass
        def _request_with_retry(self, payload): return self._raw_request(payload)
        def _render_prompt(self, key, **kwargs): return kwargs.get("prompt", "")
        @abstractmethod
        def _build_payload(self, prompt, **kwargs): pass
        @abstractmethod
        def _raw_request(self, payload): pass

# from common.gpt_client.base_client import BaseLLMClient
class OpenAIClient(BaseLLMClient):
    """
    OpenAI 模型客户端，实现 _build_payload 和 _raw_request，
    以对接 OpenAI ChatCompletion API。
    """

    def __init__(self, config: dict):
        """
        :param config: 包含 "api"、"templates"、"templates_path" 等字段的完整配置
        """
        super().__init__(config)
        provider_cfg = config.get("api", {})

        if "key" in provider_cfg:
            self.api_key = provider_cfg["key"]
        elif "key_path" in provider_cfg:
            with open(provider_cfg["key_path"], "r") as f:
                self.api_key = f.read().strip()
        elif "key_env_var" in provider_cfg:
            self.api_key = os.getenv(provider_cfg["key_env_var"])
        else:
            raise ValueError("No OpenAI API key provided via key, key_path, or key_env_var")


        models = provider_cfg.get("models", [])
        self.default_model = provider_cfg.get("default_model") or (models[0]["name"] if models else "gpt-4")
        self.default_temperature = provider_cfg.get("default_temperature", 0.7)
    # ---------------------------------------------------------
    #  构建 payload
    # ---------------------------------------------------------
    def _build_payload(self, prompt: str, **kwargs) -> dict:
        """
        构建 OpenAI ChatCompletion 请求体
        """
        model = kwargs.get("model", self.default_model)
        temperature = kwargs.get("temperature", self.default_temperature)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": ""},
                {"role": "user",   "content": prompt}
            ],
            "temperature": temperature,
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        if "n" in kwargs:
            payload["n"] = kwargs["n"]
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]
        return payload
    # ---------------------------------------------------------
    #  执行请求
    # ---------------------------------------------------------
    def _raw_request(self, payload: dict) -> dict:
        """
        执行 HTTP POST 调用到 OpenAI API，并返回 JSON 响应
        """
        api_cfg = getattr(self, 'cfg', payload)  # fallback if cfg not set
        # key = os.getenv(api_cfg.get("key_env_var", "OPENAI_API_KEY"))
        # if not key:
        #     raise EnvironmentError(f"Environment variable '{api_cfg.get('key_env_var')}' not set")

        base_url = api_cfg.get("base_url", "https://api.openai.com/v1")
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self.logger.error(f"OpenAI API error: {e}, response: {response.text}")
            raise
        return response.json()
