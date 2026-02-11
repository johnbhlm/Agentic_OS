import os
from openai import OpenAI, APIError
import urllib
import requests

# 🚫 强制关闭所有代理
for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "FTP_PROXY", "ftp_proxy"]:
    os.environ.pop(key, None)
os.environ["NO_PROXY"] = "*"

# 🧩 禁用 requests 对系统代理的信任
session = requests.Session()
session.trust_env = False
# 1. 准备工作：初始化客户端
# 建议通过环境变量配置API Key，避免硬编码。
try:
    client = OpenAI(
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
        # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key="sk-b2d24ce815fb46cf9aba319e7a5b43a1",
        # 以下是北京地域base-url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
except KeyError:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

# 2. 发起流式请求
try:
    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "请介绍2008北京奥运会"}
        ],
        stream=True,
        # 目的：在最后一个chunk中获取本次请求的Token用量。
        stream_options={"include_usage": True}
    )

    # 3. 处理流式响应
    # 使用列表推导式和join()是处理大量文本片段时最高效的方式。
    content_parts = []
    print("AI: ", end="", flush=True)
    
    for chunk in completion:
        # 最后一个chunk不包含choices，但包含usage信息。
        if chunk.choices:
            # 关键：delta.content可能为None，使用`or ""`避免拼接时出错。
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
            content_parts.append(content)
        elif chunk.usage:
            # 请求结束，打印Token用量。
            print("\n--- 请求用量 ---")
            print(f"输入 Tokens: {chunk.usage.prompt_tokens}")
            print(f"输出 Tokens: {chunk.usage.completion_tokens}")
            print(f"总计 Tokens: {chunk.usage.total_tokens}")

    full_response = "".join(content_parts)
    # print(f"\n--- 完整回复 ---\n{full_response}")

except APIError as e:
    print(f"API 请求失败: {e}")
except Exception as e:
    print(f"发生未知错误: {e}")