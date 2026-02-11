import os
from dashscope import MultiModalConversation
import dashscope 

# 若使用新加坡地域的模型，请取消下列注释
# dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

# 将xxx/eagle.png替换为你本地图像的绝对路径
# local_path = "/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/assistant_robot/common/gpt_client/qwen/image/opened_door.jpg"
# local_path = "/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/assistant_robot/common/gpt_client/qwen/image/opened_window.jpg"
local_path = "/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/assistant_robot/common/gpt_client/qwen/image/desk_top.jpg"


image_path = f"file://{local_path}"
# text = "检查一下门是不是已经关上？"
# text = "帮我检查一下窗户是不是已经关上了？"
text = "帮我看下我的笔记本是不是在我的办公桌上？另外看一下我的电脑屏幕是不是关闭了？"
messages = [
                {'role':'user',
                'content': [{'image': image_path},
                            {'text': text}]}]
response = MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    # api_key=os.getenv('DASHSCOPE_API_KEY'),
    api_key="sk-b2d24ce815fb46cf9aba319e7a5b43a1",
    model='qwen3-vl-plus',  # 此处以qwen3-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
    messages=messages)

print("👤 用户指令：",text)
print("🎯 模型 qwen3-vl-plus 输出：")
print(response["output"]["choices"][0]["message"].content[0]["text"])