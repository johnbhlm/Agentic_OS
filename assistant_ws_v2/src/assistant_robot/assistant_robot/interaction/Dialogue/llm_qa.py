import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LLMQA:
    """
    多轮问答管理模块，使用大模型的 'chat' 模板处理用户问答。
    模板 key: "chat"
    """

    def __init__(self, gpt_client):
        """
        :param gpt_client: 在 main.py 中注入的统一 GPT 客户端实例
        """
        self.llm = gpt_client

    # def answer(self, question: str,context: Optional[str] = None) -> str:
    #     """
    #     对用户的提问进行回答。

    #     :param question: 用户的当前提问文本
    #     :param context:  上下文对话历史（多轮 QA 时传入），格式为字符串
    #     :return:        生成的回答文本
    #     """
    #     # 调用 chat 模板，传入 query 和可选的上下文
    #     # resp = self.llm.chat(
    #     #     template_key="llm_qa",
    #     #     query=question,
    #     #     context=context or ""
    #     # ).strip()

    #     logger.info("QA raw response: %s", resp)
    #     return resp

    def answer(self, question: str,history: Optional[str] = None) -> str:
        """
        对用户的提问进行回答。

        :param question: 用户的当前提问文本
        :param context:  上下文对话历史（多轮 QA 时传入），格式为字符串
        :return:        生成的回答文本
        """
        # 调用 chat 模板，传入 query 和可选的上下文
        # resp = self.llm.chat(
        #     template_key="llm_qa",
        #     query=question,
        #     context=context or ""
        # ).strip()

        # for Qwen
        resp = self.llm.chat(
            template_key="llm_qa",
            user_instruction=question,
            history=history,
            extra_body={
                "enable_search": True,
                "search_options": {
                    "forced_search": True  # 强制联网搜索
                }
            },
        ).strip()

        logger.info("QA raw response: %s", resp)
        return resp
