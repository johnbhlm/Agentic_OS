# import os
# import urllib
# import requests
# from openai import OpenAI

# # #🚫 强制关闭所有代理
# # for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "FTP_PROXY", "ftp_proxy"]:
# #     os.environ.pop(key, None)
# # os.environ["NO_PROXY"] = "*"

# # # 🧩 禁用 requests 对系统代理的信任
# # session = requests.Session()
# # session.trust_env = False

# OPENAI_API_KEY="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"


# import json
# import http.client
# import ssl

# # ====== 1. 读取 Key ======
# api_key = OPENAI_API_KEY #os.environ.get("OPENAI_API_KEY")
# if not api_key:
#     raise RuntimeError("OPENAI_API_KEY not set")

# # ====== 2. 构造 HTTPS 连接 ======
# conn = http.client.HTTPSConnection(
#     "api.openai.com",
#     context=ssl.create_default_context(),
#     timeout=60,
# )

# # ====== 3. 请求头 ======
# headers = {
#     "Authorization": f"Bearer {api_key}",
#     "Content-Type": "application/json",
# }

# # ====== 4. 请求体（Responses API）=====
# payload = {
#     "model": "gpt-4o",
#     "input": "请只返回一个单词：PINEAPPLE",
#     "max_output_tokens": 20,
# }

# print(">>> sending request to GPT-4o ...")

# conn.request(
#     "POST",
#     "/v1/responses",
#     body=json.dumps(payload),
#     headers=headers,
# )

# # ====== 5. 读取响应 ======
# resp = conn.getresponse()
# raw = resp.read().decode("utf-8")

# print("HTTP status:", resp.status)
# print("Raw response:")
# print(raw)

# # ====== 6. 判断是否真的调用到 GPT ======
# if resp.status != 200:
#     raise RuntimeError("❌ HTTP 层失败，未调用 GPT")

# data = json.loads(raw)

# if "model" not in data or "output" not in data:
#     raise RuntimeError("❌ 返回结构不是 OpenAI GPT")

# print("✅ Model:", data["model"])

# found = False
# for item in data["output"]:
#     if item.get("type") == "message":
#         for c in item.get("content", []):
#             if c.get("type") == "output_text":
#                 print("✅ GPT Output:", c["text"])
#                 found = True

# if not found:
#     raise RuntimeError("❌ 没有找到 GPT 输出文本")

# print("🎉 SUCCESS: GPT-4o is working")


# # import requests

# # proxies = {
# #     "http":  "socks5h://127.0.0.1:12334",
# #     "https": "socks5h://127.0.0.1:12334",
# # }

# # r = requests.get(
# #     "https://api.openai.com/v1/models",
# #     proxies=proxies,
# #     headers={"Authorization": "Bearer sk-xxxx"},
# #     timeout=20,
# # )

# # print(r.status_code)
# # print(r.text)


# export OPENAI_API_KEY="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"

from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4o",
    input="只输出一个单词：PINEAPPLE",
    max_output_tokens=10,
)

print(response.output_text)
