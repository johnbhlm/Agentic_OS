import os
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI

import urllib
import requests


# # 🚫 强制关闭所有代理
# for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "FTP_PROXY", "ftp_proxy"]:
#     os.environ.pop(key, None)
# os.environ["NO_PROXY"] = "*"

# # 🧩 禁用 requests 对系统代理的信任
# session = requests.Session()
# session.trust_env = False

# LLM 配置
llm_cfg = {
    "model": "qwen-plus-latest",
    "model_server": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx"
    # "api_key": os.getenv("DASHSCOPE_API_KEY"),
    "api_key": "sk-b2d24ce815fb46cf9aba319e7a5b43a1",
}

# 系统消息
system = "你是会天气查询、地图查询、网页部署的助手"

# 工具列表
tools = [
    {
        "mcpServers": {
            "amap-maps": {
                "type": "sse",
                # 替换为您的 URL
                "url": "https://mcp.api-inference.modelscope.net/2c30b7dc5d024b/sse",
            },
            "edgeone-pages-mcp": {
                "type": "sse",
                # 替换为您的 URL
                "url": "https://mcp.api-inference.modelscope.net/6ade05ae13ec43/sse",
            },
        }
    }
]

# 创建助手实例
bot = Assistant(
    llm=llm_cfg,
    name="助手",
    description="高德地图、天气查询、公网链接部署",
    system_message=system,
    function_list=tools,
)
WebUI(bot).run()