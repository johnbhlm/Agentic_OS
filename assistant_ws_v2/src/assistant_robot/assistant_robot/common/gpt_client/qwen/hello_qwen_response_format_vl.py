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

client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    # api_key=os.getenv("DASHSCOPE_API_KEY"),
    api_key="sk-b2d24ce815fb46cf9aba319e7a5b43a1",
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen-vl-max",
    messages=[
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful assistant."}],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "http://duguang-labelling.oss-cn-shanghai.aliyuncs.com/demo_ocr/receipt_zh_demo.jpg"
                    },
                },
                {"type": "text", "text": "提取图中ticket(包括 travel_date、trains、seat_num、arrival_site、price)和 invoice 的信息（包括 invoice_code 和 invoice_number ），请输出包含 ticket 和 invoice 数组的JSON"},
            ],
        },
    ],
    response_format={"type": "json_object"}
)
json_string = completion.choices[0].message.content
print(json_string)