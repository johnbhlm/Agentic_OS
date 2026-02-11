# import os
# # import urllib
# import requests
# # from openai import OpenAI

# # 强制关闭所有代理
# for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "FTP_PROXY", "ftp_proxy"]:
#     os.environ.pop(key, None)
# os.environ["NO_PROXY"] = "*"

# # 禁用 requests 对系统代理的信任
# session = requests.Session()
# session.trust_env = False



# export OPENAI_API_KEY="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"

# from openai import OpenAI
# client = OpenAI()

# response = client.responses.create(
#     model="gpt-5-nano",
#     input="Write a one-sentence bedtime story about a unicorn."
# )

# print(response.output_text)



import os
import openai
# from openai import OpenAI
import requests

# 设置 API Key（也可以直接在环境变量中设置 OPENAI_API_KEY）
openai.api_key = os.getenv("OPENAI_API_KEY", "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")

# # 最新版本
# from openai import OpenAI
# client = OpenAI()

# response = client.responses.create(
#     model="gpt-5-nano",
#     input="Write a one-sentence bedtime story about a unicorn."
# )

# print(response.output_text)

# openai1.60 
# from openai import OpenAI
# client = OpenAI(openai.api_key)

# response = client.chat.completions.create(
#     model="gpt-5-nano",
#     messages=[
#                 {"role": "system", "content": ""},
#                 {"role": "user",   "content": "Write a one-sentence bedtime story about a unicorn."}
#             ],
# )

# print(response.choices[0]["message"]["content"])


import os
import openai

# 方式一：从环境变量读取 API Key
# export OPENAI_API_KEY="你的API_KEY"
# openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_key = os.getenv("OPENAI_API_KEY", "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")


# 方式二：直接赋值
openai.api_key = "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"

# 调用 Chat Completions
response = openai.chat.completions.create(
    model="gpt-5-mini",  # 或 "gpt-3.5-turbo"
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a one-sentence bedtime story about a unicorn."}
    ],
    temperature=0.7
)

# 输出返回内容
print(response.choices[0].message.content)


try:
    # 测试获取可用模型列表
    models = openai.Model.list()
    print("✅ API 连接成功！可用模型列表如下：")
    for m in models.data:
        print(" -", m.id)
    
    # client = OpenAI()
    # response = client.responses.create(
    #     model="gpt-5-nano",
    #     input="Write a one-sentence bedtime story about a unicorn."
    # )

    # print(response.output_text)

    payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": ""},
                {"role": "user",   "content": "Hello"}
            ],
            "temperature": 0.7,
        }
    

    # base_url = api_cfg.get("base_url", "")
    url = f"https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    print(response.json())
    print(response.json()["choices"][0]["message"]["content"])


except Exception as e:
    print("❌ API 访问失败！错误信息：", e)
