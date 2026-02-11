import os
from openai import OpenAI, APIError
import urllib
import requests
import yaml
import json

# 🚫 强制关闭所有代理
for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "FTP_PROXY", "ftp_proxy"]:
    os.environ.pop(key, None)
os.environ["NO_PROXY"] = "*"

# 🧩 禁用 requests 对系统代理的信任
session = requests.Session()
session.trust_env = False

# 初始化OpenAI客户端
client = OpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    # api_key=os.getenv("DASHSCOPE_API_KEY"),
    api_key="sk-b2d24ce815fb46cf9aba319e7a5b43a1",
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# =======================================
# 🧠 读取 YAML Prompt 文件
# =======================================
with open("/home/maintenance/Code/instruction/assistant_ws_v2/src/assistant_robot/config/prompts/clarifier_prompt_QWen.yaml", "r", encoding="utf-8") as f:
    prompt_yaml = yaml.safe_load(f)

system_prompt = prompt_yaml["messages"][0]["content"]
user_prompt_template = prompt_yaml["messages"][1]["content"]

# =======================================
# 🔧 辅助函数：生成用户输入 JSON
# =======================================
def build_user_prompt(instruction, history="", asked_questions="", last_clarified_command=""):
    """将模板变量替换为实际值"""
    user_content = (
        user_prompt_template
        .replace("{{ instruction }}", json.dumps(instruction, ensure_ascii=False))
        .replace("{{ history }}", json.dumps(history, ensure_ascii=False))
        .replace("{{ asked_questions }}", json.dumps(asked_questions, ensure_ascii=False))
        .replace("{{ last_clarified_command }}", json.dumps(last_clarified_command, ensure_ascii=False))
    )
    return user_content

# =======================================
# 🔁 多轮澄清测试函数
# =======================================
def clarify_instruction(instruction):
    """执行多轮澄清流程"""
    history = ""
    asked_questions = ""
    last_clarified_command = ""
    round_num = 1

    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""     # 定义完整回复

    messages = []
    conversation_idx = 1

    while True:
        is_answering = False  
        print(f"\n🧭 第 {round_num} 轮用户输入：{instruction}")

        user_prompt = build_user_prompt(
            instruction,
            history,
            asked_questions,
            last_clarified_command
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 🔮 调用 Qwen 模型
        completion = client.chat.completions.create(
            model="qwen-plus",  # qwen-plus-2025-04-28 或 qwen-max、qwen-turbo 等
            messages=messages,
            # extra_body={"enable_thinking": True},
            stream=True,
        )

        print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")
        for chunk in completion:
            # 如果chunk.choices为空，则打印usage
            if not chunk.choices:
                print("\nUsage:")
                print(chunk.usage)
            else:
                delta = chunk.choices[0].delta
                # 打印思考过程
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content != None:
                    print(delta.reasoning_content, end='', flush=True)
                    reasoning_content += delta.reasoning_content
                else:
                    # 开始回复
                    if delta.content != "" and is_answering is False:
                        print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                        is_answering = True
                    # 打印回复过程
                    print(delta.content, end='', flush=True)
                    answer_content += delta.content
        # 将模型回复的content添加到上下文中
        messages.append({"role": "assistant", "content": answer_content})
        print("\n")

        response = completion.choices[0].message.content.strip()
        print("\n🤖 模型输出：")
        print(response)

        # 解析 JSON
        try:
            response_json = json.loads(response)
        except json.JSONDecodeError:
            print("❌ 错误：模型输出不是有效 JSON。")
            break

        # 提取字段
        need_clarification = response_json.get("need_clarification", False)
        clarified_command = response_json.get("clarified_command", "")
        missing_info = response_json.get("missing_info", "")
        final_command = response_json.get("final_command", "")

        # 更新上下文
        if need_clarification:
            print(f"\n❓ 模型请求澄清: {missing_info}")
            history = instruction
            asked_questions = missing_info
            last_clarified_command = clarified_command
            instruction = input("\n👤 用户回答: ")  # 人工输入下一轮回答
            round_num += 1
        else:
            print(f"\n✅ 澄清完成！最终命令：{final_command}")
            break

# =======================================
# 🚀 启动测试
# =======================================
if __name__ == "__main__":
    print("\n====== 智能机器人多轮澄清测试 ======\n")
    first_instruction = input("请输入用户初始指令: ")
    clarify_instruction(first_instruction)