import os
import logging
import requests
import time
import yaml
import json
from openai import OpenAI
from assistant_robot.common.gpt_client.base_client import BaseLLMClient
# from base_client import BaseLLMClient

class QwenClient(BaseLLMClient):
    """
    Qwen (阿里云百炼 / DashScope) 模型客户端
    继承 BaseLLMClient，独立实现 Qwen API 调用逻辑
    """

    def __init__(self, config: dict):
        # 🚫 强制关闭所有代理
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "FTP_PROXY", "ftp_proxy"]:
            os.environ.pop(key, None)
        os.environ["NO_PROXY"] = "*"

        # 🧩 禁用 requests 对系统代理的信任
        session = requests.Session()
        session.trust_env = False
        """
        初始化 Qwen 客户端
        :param config: 含 "api"、"templates" 等字段的配置
        """
        # 调用父类初始化
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)

        provider_cfg = config.get("api", {})
        self.cfg = provider_cfg
        self.templates_path = config.get("templates_path", "")
        self.template_map = config.get("templates", {})

        self.messages_cache =[]
        self.sys_tmp = False

        # 读取 API key (优先级: key > key_path > key_env_var)
        if "key" in provider_cfg:
            self.api_key = provider_cfg["key"]
        elif "key_path" in provider_cfg:
            with open(provider_cfg["key_path"], "r") as f:
                self.api_key = f.read().strip()
        elif "key_env_var" in provider_cfg:
            self.api_key = os.getenv(provider_cfg["key_env_var"])
        else:
            raise ValueError("No Qwen API key provided via key, key_path, or key_env_var")

        # ---- 基础配置 ----
        # 北京地域： https://dashscope.aliyuncs.com/compatible-mode/v1
        # 新加坡地域： https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        self.base_url = provider_cfg.get(
            "base_url",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        models = provider_cfg.get("models", [])
        self.default_model = provider_cfg.get("default_model") or (models[0]["name"] if models else "qwen-plus")
        self.default_temperature = provider_cfg.get("default_temperature", 0.7)
        self.timeout = provider_cfg.get("timeout", 60)

        # ✅ 使用 OpenAI SDK 初始化客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Initialized QwenClient with model: {self.default_model}")

    # ---------------------------------------------------------
    #  构建 payload
    # ---------------------------------------------------------
    def _build_payload(self, messages, **kwargs) -> dict:
        """
        构建 Qwen ChatCompletion 请求体
        """
        model = kwargs.get("model", self.default_model)
        temperature = kwargs.get("temperature", self.default_temperature)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        # print("*****************kwargs：",kwargs)
        # 通用参数
        for key in ["max_tokens", "top_p", "presence_penalty", "stop"]:
            if key in kwargs:
                payload[key] = kwargs[key]
        if "extra_body" in kwargs:
            payload["extra_body"] = kwargs["extra_body"]
            # extra_body={"enable_search": True, "enable_thinking": True}

        if "stream" in kwargs:
            payload["stream"] = kwargs["stream"]
        
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]

        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]

        if "parallel_tool_calls" in kwargs:
            payload["parallel_tool_calls"] = kwargs["parallel_tool_calls"]

        return payload
    
    # ---------------------------------------------------------
    #  执行请求
    # ---------------------------------------------------------
    # def _raw_request(self, payload: dict) -> dict:
    #     """
    #     发送 HTTP 请求到 Qwen DashScope 兼容接口
    #     """
        
    #     url = f"{self.base_url.rstrip('/')}/chat/completions"
    #     headers = {
    #         "Authorization": f"Bearer {self.api_key}",
    #         "Content-Type": "application/json",
    #     }

    #     self.logger.debug(f"Qwen Request URL: {url}")
    #     self.logger.debug(f"Payload: {payload}")

    #     resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
    #     try:
    #         resp.raise_for_status()
    #     except requests.HTTPError as e:
    #         self.logger.error(f"Qwen API error: {e}, response: {resp.text}")
    #         raise

    #     return resp.json()
    
    def _raw_request(self, payload: dict) -> dict:
        """
        调用 OpenAI SDK (Qwen 兼容模式)
        """
        start = time.time()
        try:
            completion = self.client.chat.completions.create(**payload)
            resp = completion.model_dump()  # 转成普通 dict
        except Exception as e:
            self.logger.error(f"Qwen SDK request error: {e}")
            raise
        elapsed = time.time() - start
        self.logger.info(f"Qwen SDK request took {elapsed:.2f}s")
        return resp
    
    def _parse_response(self, resp: dict) -> str:
        """
        提取内容
        """
        try:
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"Failed to parse Qwen response: {e}")
            raise
    
    def chat(self, template_key: str,user_instruction:str, **kwargs) -> str:
        """
        通用接口：根据模板 key + 参数渲染 prompt，
        构建 payload，发送请求并解析返回内容。
        """
        messages = []
        prompt_yaml = self.prompt_mgr.render_ymal(template_key, **kwargs)

        system_prompt = prompt_yaml["messages"][0]["content"]
        messages.append({"role": "system", "content":system_prompt})
       
        # 2. 构建请求体
        if "history" in kwargs:
            # self.messages_cache.append({"role": "assistant", "content": kwargs["history"]})
            messages.append({"role": "assistant", "content": kwargs["history"]})

        # self.messages_cache.append({"role": "user", "content": user_instruction})
        messages.append({"role": "user", "content": user_instruction})

        payload = self._build_payload(messages,**kwargs)
        # 3. 发送请求
        start = time.time()
        resp = self._request_with_retry(payload)
        elapsed = time.time() - start
        self.logger.info(f"[{self.__class__.__name__}] {template_key} took {elapsed:.2f}s")
        # 4. 解析响应
        return self._parse_response(resp)


if __name__ == "__main__":
    # # 🚫 强制关闭所有代理
    # for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "FTP_PROXY", "ftp_proxy"]:
    #     os.environ.pop(key, None)
    # os.environ["NO_PROXY"] = "*"

    # # 🧩 禁用 requests 对系统代理的信任
    # session = requests.Session()
    # session.trust_env = False

    # # 🧪 本地测试
    # cfg = {
    #     "api": {
    #         "key_path": "/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/config/keys/qwen_key.txt",
    #         "default_model": "qwen-flash",
    #         "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    #         "timeout": 30,
    #     }
    # }

    # qwen = QwenClient(cfg)

    # prompt = "请抽取用户的姓名、年龄、邮箱、爱好信息，以JSON格式返回。\n我叫张三，今年34岁，邮箱是zhangsan@example.com，平时喜欢打篮球和旅游。"

    # payload = qwen._build_payload(prompt)
    # result = qwen._raw_request(payload)

    # print(result["choices"][0]["message"]["content"])



    import sys
    from factory import ProviderFactory
    sys.path.append("..") 
    from utils import load_yaml_test

    # gpt_cfg = load_yaml_test("/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/config/gpt_config.yaml")
    gpt_cfg = load_yaml_test("gpt_config.yaml")
    # print(gpt_cfg)
    qwen_client = ProviderFactory.create(gpt_cfg)

    result = qwen_client.chat(
        template_key="llm_qa",  # 或任意模板  llm_planner  llm_intent   llm_clarifier  llm_qa
        # user_instruction="将绿色桌子上的两个狮子放到黑色桌子上，然后将圆桌上的三个恐龙放到绿色桌子上",
        # user_instruction="先到白色桌子，然后到黑色桌子，然后到电视柜，最后回到沙发",
        # user_instruction="去白色桌子，然后将桌子上的狮子放到沙发，然后到回到白色桌子",

        # user_instruction="讲个笑话吧",
        user_instruction="今天是什么日子？现在几点了？北京现在的气温怎么样？",
        # user_instruction="将桌子上的玩偶放到电视柜上", 

        # user_instruction="将这个玩偶放到那里",
        # user_instruction="将沙发上的狮子拿给我",
        # user_instruction="我想要那个黄色的玩偶",
        # user_instruction="将白桌子上的几个鸭子都放到沙发上",

        # user_instruction="我要沙发上的鸭子",
        # user_instruction="将沙发上的恐龙放到白色桌子",
        # user_instruction="导航到白色桌子",
        extra_body={
            # "enable_reasoning": True,   # 开启“思考模式”
            "enable_search": True,
                # "search_options": {
                #     "forced_search": True  # 强制联网搜索
                # }
        },
                
        # response_format={"type": "json_object"},
        # stream=True
    )

    print("✅ Qwen 返回：")
    # print("✅ Qwen Plus 返回：")
    # print("✅ Qwen3 Max 返回：")
    # print("✅ Deepseek-R1 返回：")
    # print("✅ Kimi 返回：")
    print(result)
