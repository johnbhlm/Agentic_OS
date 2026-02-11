import logging
import json
from typing import Tuple, List

# # 获取当前文件路径：.../assistant_robot/planner/llm_based
# import os, sys
# current_dir = os.path.dirname(__file__)
# # 添加 assistant_robot 根目录到 sys.path
# project_root = os.path.abspath(os.path.join(current_dir, "../../"))
# sys.path.append(project_root)

# from common.utils import load_yaml,init_logging
# from common.gpt_client.factory import ProviderFactory


logger = logging.getLogger(__name__)

class ClarifyManager:
    """
    基于 LLM 判断任务指令是否足够清晰。如果不清晰，返回需要向用户询问的澄清问题。
    支持多轮澄清，返回 (need_clarification, question, clarified_command)
    """

    def __init__(self, gpt_client):
        """
        :param gpt_client: 统一的 GPT 客户端实例
        """
        self.llm = gpt_client
    
    def parse_llm_response(self, text: str) -> dict:
        """
        解析 LLM 返回的纯文本格式：
        need_clarification: true
        clarified_command: "..."
        missing_info: "..."
        """
        result = {}
        for line in text.strip().split('\n'):
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip().strip('"')  # 去除 key 两侧多余双引号
            value = value.strip().rstrip(',').strip()  # 去除 value 尾部逗号和两侧空白
            value = value.strip('"')  # 去除 value 两侧双引号

            if key == 'need_clarification':
                value = value.lower() == 'true'
            result[key] = value
        return result
    
    def needs_clarification(
        self,
        full_instruction: str,
        history: List[str],
        clarify_history: List[str],
        last_clarified_command: str = ""
    ) -> Tuple[bool, str, str]:
        """
        判断指令是否清晰，若不清晰则生成澄清问题。

        :param full_instruction: 用户的完整任务指令（包含原始+补充）
        :param history: 当前 session 的对话历史（用于 LLM 提取上下文）
        :param clarify_history: 之前所有澄清问题（避免重复问）
        :param last_clarified_command: 上一次澄清后的指令（用于多轮累积）
        :return: (是否需要澄清, 澄清问题, 累积的 clarified_command)
        """
        context = "\n".join(history)
        clarifies = "\n".join(f"- {q}" for q in clarify_history)

        # 调用 LLM，根据 clarifier_prompt.j2 渲染
        # print("full_instruction:",full_instruction)
        # print("context:",context)
        # print("clarifies:",clarifies)
        # print("last_clarified_command:",last_clarified_command)
        
        # resp = self.llm.chat(
        #     template_key="llm_clarifier",
        #     instruction = full_instruction,
        #     history = context,
        #     asked_questions = clarifies,
        #     last_clarified_command = last_clarified_command
        # )#.strip()

        # For Qwen
        history_info = [
            {"context":context,"asked_questions":clarifies,"last_clarified_command":last_clarified_command}
        ]
        resp = self.llm.chat(
            template_key="llm_clarifier",
            user_instruction = full_instruction,
            history = str(history_info)
        )#.strip()


        # logger.info("Clarify raw response: %s", resp)
        # print("Clarify raw response: %s", resp)

        try:
            data = self.parse_llm_response(resp)
            # print("data:",data)
        except Exception as e:
            logger.warning("解析 LLM 返回格式失败，默认认为指令清晰: %s, error: %s", resp, e)
            return False, "", last_clarified_command

        need_clarification = data.get("need_clarification", True)
        question = data.get("missing_info", "").strip()
        clarified_command = data.get("clarified_command", full_instruction).strip()
        final_command = data.get("final_command", full_instruction).strip()

        if not clarified_command and last_clarified_command:
            clarified_command = last_clarified_command
        # print("need_clarification:",need_clarification)
        # print("question:",question)
        # print("clarified_command:",clarified_command)
        return need_clarification, question, clarified_command, final_command
        
        # # 解析 LLM 输出
        # try:
        #     data = json.loads(resp)            
        # except json.JSONDecodeError:
        #     # 如果不是有效 JSON，则默认认为不需要澄清
        #     logger.warning("Clarify response 非 JSON，默认认为指令清晰: %s", resp)
        #     return False, "",last_clarified_command
        
        # need_clarification = bool(data.get("need_clarification", True))
        # question = data.get("missing_info", "").strip()
        # clarified_command = data.get("clarified_command", full_instruction).strip()
        
        # # 如果模型没有生成 clarified_command，就继承上一轮的
        # if not clarified_command and last_clarified_command:
        #     clarified_command = last_clarified_command

        # return need_clarification, question, clarified_command
    
        

if __name__ == "__main__":
    # gpt_cfg = load_yaml("gpt_config.yaml")
    # gpt_client = ProviderFactory.create(gpt_cfg)
    # clarifier = ClarifyManager(gpt_client=gpt_client)
    # nl_instruction ="把小熊玩偶从红色椅子上拿起来放到沙发上"
    # nl_instruction ="把苹果从红色椅子上拿起来放到沙发上"
    # nl_instruction ="把那个东西放到冰箱里"
    # nl_instruction ="把圆桌上牛奶放到方桌上"
    # nl_instruction ="擦擦桌子，然后把圆桌上牛奶放到方桌上"
    # nl_instruction ="导航到白色椅子"
    # nl_instruction ="导航到红色椅子"
    nl_instruction ="到红色椅子"
    # history=[]
    # clarify_qs = []
    # last_clarified_command =""
    # # planner.plan(nl_instruction)
    # need_clarify, clar_q,clarified_cmd = clarifier.needs_clarification(
    #                 full_instruction=nl_instruction,
    #                 history=history,
    #                 clarify_history=clarify_qs,
    #                 last_clarified_command=last_clarified_command)
    
    # print(need_clarify)
