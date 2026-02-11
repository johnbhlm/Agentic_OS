import os,sys
import logging
import json

# # 获取当前文件路径：.../assistant_robot/planner/llm_based
# current_dir = os.path.dirname(__file__)
# # 添加 assistant_robot 根目录到 sys.path
# project_root = os.path.abspath(os.path.join(current_dir, "../../"))
# print(project_root)
# sys.path.append(project_root)

logger = logging.getLogger(__name__)

class LLM_Planner:
    def __init__(self,gpt_client):
        self.planner = gpt_client
    
    def parse_result(self, action_string):
        lines = action_string.strip().splitlines()

        # If LLM wraps output with triple backticks, strip them
        if lines[0].startswith("```"):
            lines = lines[1:]  # remove opening ```
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]  # remove closing ```

        return "\n".join(lines)
    
    def _is_action_list(self, text: str) -> bool:
        """
        判断返回是否为动作列表（每行 "N. action ..."）
        """
        valid_prefixes = ("pick", "place", "go-to")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return False
        for l in lines:
            # 检查行号 + 动作格式
            if not l[0].isdigit() or "." not in l:
                return False
            try:
                _, action = l.split(".", 1)
            except ValueError:
                return False
            if not action.strip().startswith(valid_prefixes):
                return False
        return True
    
    def plan(self,nl_instruction: str, context: str = None) -> list[str]:
        """
        将自然语言指令转为按行拆分的步骤列表
        :param nl_instruction: 用户的自然语言任务描述
        :param context: 可选，上下文信息
        :return: 
        - 成功时: {"status": "success", "actions": [...], "error": None, "raw": "..."}
        - 失败时: {"status": "error", "actions": [], "error": {...}, "raw": "..."}
        """
        # 1. 调用统一的 plan 接口，渲染 prompt_llm_planner.j2
        try:
            # 确保模板里使用的是 {{ query }} 变量
            raw = self.planner.chat(
                template_key="llm_planner",
                user_instruction=nl_instruction,
                context=context or ""
            )
            # logger.info("LLM 规划原始返回：\n%s", raw)

            # 2. 清理 code fence
            cleaned = self.parse_result(raw)
            print("\n")
            print(" ****************** 🎯 LLM parser instruction result ******************")
            # print(cleaned)
            # print("\n")

            if cleaned.startswith("{") and cleaned.endswith("}"):
                try:
                    err_obj = json.loads(cleaned)
                    # print(err_obj.get("message"))
                    return {
                        "status": "error",
                        "actions": [],
                        "error": {
                            "type": err_obj.get("error"),
                            "message": err_obj.get("question") or err_obj.get("message") or err_obj.get("reason"),
                            "language": err_obj.get("language", "unknown")
                        },
                        "raw": cleaned
                    }
                except json.JSONDecodeError:
                    logger.error("返回 JSON 解析失败: %s", cleaned)
                    return {"status": "error", "actions": [], "error": {"type": "invalid_json", "message": cleaned}, "raw": cleaned}
            if self._is_action_list(cleaned):
                print(cleaned)
                print("\n")
                # actions = [line.strip().split(".", 1)[1].s
                # trip() for line in cleaned.splitlines() if line.strip()]
                actions = [line.strip().split(".")[1] for line in cleaned.splitlines() if line.strip()]
                return {"status": "success", "actions": actions, "error": None, "raw": cleaned}
                # return actions
                # # 3. 按行拆分、去除空行
                # actions = [line.strip().split(".")[1] for line in cleaned.splitlines() if line.strip()]
                # # print(actions)
                # return actions
            logger.error("LLM 返回无法识别: %s", cleaned)
            return {"status": "error", "actions": [], "error": {"type": "unrecognized", "message": cleaned}, "raw": cleaned}
        
        except Exception as e:
            logger.error("LLM 规划失败：%s", e, exc_info=True)
            return {"status": "error", "actions": [], "error": {"type": "exception", "message": str(e)}, "raw": ""}
    

if __name__ == "__main__":
    # from common.utils import load_yaml_test,init_logging
    # from common.gpt_client.factory import ProviderFactory

    # gpt_cfg = load_yaml_test("gpt_config.yaml")
    # gpt_client = ProviderFactory.create(gpt_cfg)
    # planner = LLM_Planner(gpt_client=gpt_client)
    nl_instruction ="将红色椅子上的小熊放到白色椅子上"
    # planner.plan(nl_instruction)

   
    # nl_instruction ="You are next to the bed, putting the plates on the dining table into the sink, heating the milk on the dining table in the microwave, and then taking it to the dining table."
    
    
    #L0
    # nl_instruction ="将沙发上小熊玩偶的拿到床上"
    # nl_instruction ="把餐桌上的苹果和牛奶放进冰箱"
    # nl_instruction ="Move the doll from the sofa onto the bed"
    # nl_instruction ="Place the orange and cola from the coffee table into the fridge."
    # nl_instruction ="我在餐桌旁，将茶几上的橘子放到冰箱中，将冰箱中的牛奶拿到餐桌"
    
    #L1
    # nl_instruction ="将茶几上的几个苹果放到学习桌上"
    # nl_instruction ="Put the bottles of water on the dining table in the refrigerator"

    #L2
    # nl_instruction ="把东西放进冰箱。"
    # nl_instruction ="将床上抱枕放到那里"  
    # nl_instruction ="Put the item on the bed into the fridge."
    # nl_instruction ="Put the pillow on the bed over there"
    # nl_instruction ="把餐桌的物品都放好。"  
    # nl_instruction ="Organize everything on the study table."
    
    #L3
    # nl_instruction ="把那边的东西整理一下"
    # nl_instruction ="Pick it up and go."
    
    # planner.plan(nl_instruction)
    