import logging
import time 
from typing import Dict, Optional
from uuid import uuid4
import rclpy
import threading

from assistant_robot.interaction.Dialogue.llm_intent_router import LLMIntentRouter
from assistant_robot.interaction.Dialogue.llm_clarify import ClarifyManager
from assistant_robot.interaction.Dialogue.llm_qa import LLMQA
from assistant_robot.common.utils import is_end_session,truncate_by_duration, is_rest

# from assistant_robot_msgs.msg import VLNStatus,VLAStatus
# from assistant_robot.memory.ros_interface import VLA_ResetPublisher,VLA_ResetSubscriber,VLN_ResetPublisher,VLN_ResetSubscriber
# from assistant_robot_msgs.msg import ResetVLA, ResetVLN

logger = logging.getLogger(__name__)

class Session:
    def __init__(self, session_id: Optional[str] = None):
        self.id = session_id or str(uuid4())
        self.state = "NEW"
        self.history = []             # List[str]
        self.intent = None            # "QA" 或 "PLAN"
        self.clarify_qs = []          # 针对 plan需要澄清问题
        self.plan_state = "INIT" # INIT  PLAN_CLARIFY   PLAN_EXECUTE
        self.last_clarified_command ="" #保存当前累积指令

class DialogueManager:
    def __init__(self, gpt_client,speech_mannger,node):
        self.sessions: Dict[str, Session] = {}
        self.intent_router = LLMIntentRouter(gpt_client)
        self.clarifier = ClarifyManager(gpt_client)
        self.qa_manager = LLMQA(gpt_client)
        self.speech = speech_mannger
        self.session_timeout = 180.0 # 对话最长时长（秒），默认 3 分钟
        # self.session_time = 0
        self.session_id = None

        # # === Reset 发布 / 订阅 ===
        # self._vla_reset_done = False
        # self._vln_reset_done = False
        # self._vla_reset_pub = VLA_ResetPublisher(node)
        # self._vla_reset_sub = VLA_ResetSubscriber(node, self._on_vla_status)
        # self._vln_reset_pub = VLN_ResetPublisher(node)        
        # self._vln_reset_sub = VLN_ResetSubscriber(node, self._on_vln_status)

        # # === 用 Event 控制同步等待 ===
        # self._vla_reset_event = threading.Event()
        # self._vln_reset_event = threading.Event()

    # ===============================
    # VLA / VLN Reset 回调
    # ===============================
    # def _on_vla_status(self, msg: ResetVLA):
    #     if msg.reset_status==1:   # 假设 1 表示 reset 成功
    #         logger.info("VLA reset 完成")
    #         # self._vla_reset_done = True
    #         self._vla_reset_event.set()

#     def _on_vln_status(self, msg: ResetVLN):
#         if msg.reset_status==1:
#             # logger.info("VLN reset 完成")
#             self._vln_reset_event.set()

#    # ========== Reset 等待函数 ==========
#     def _wait_for_reset(self, event: threading.Event, name: str, timeout: float = 10.0) -> bool:
#         ok = event.wait(timeout=timeout)
#         if not ok:
#             logger.info(f"⚠️ 等待 {name} Reset 超时")
#         return ok
    
    # ========== 串行执行“休息一下” ==========
    def handle_rest(self):
        # self.speech._speak("收到休息指令，正在准备休息。")

        # # 1. VLA Reset
        # self._vla_reset_event.clear()
        # self._vla_reset_pub.publish()
        # self.speech._speak("正在重置 VLA 系统...")
        # if not self._wait_for_reset(self._vla_reset_event, "VLA"):
        #     self.speech._speak("VLA 重置失败，请检查系统。")
        #     # return

        # # 2. VLN Reset
        # self._vln_reset_event.clear()
        # self._vln_reset_pub.publish()
        # self.speech._speak("正在重置导航程序。")
        # if not self._wait_for_reset(self._vln_reset_event, "VLN"):
        #     self.speech._speak("导航程序重置失败，请检查系统。")
        #     return
        
        # 3. 导航到休息点（这里留接口）
        self.speech._speak("好的，我将导航到休息区。")
        # 重置对话
        self.speech.reset()
        self.dialogue_reset()
        
        final_cmd = "休息一下。"
        # self.speech._speak( "我要休息了，如有需要请再次唤醒我。")             
        return final_cmd

    # ===============================
    # 重置对话状态
    # ===============================
    def dialogue_reset(self):
        self.state = "NEW"
        self.history = []
        self.intent = None 
        self.clarify_qs = []
        self.plan_state = "INIT"
        self.last_clarified_command =""
        self.session_id = None

    # ===============================
    # 处理用户输入
    # ===============================
    def handle(self, user_input: str,session_id: Optional[str] = None):
        # 获取或创建会话
        sess = self.sessions.get(self.session_id) if self.session_id else None
        
        if not sess:
            sess = Session(self.session_id)
            self.sessions[sess.id] = sess
            self.session_start_t = time.time()
            self.session_id = sess.id
            logger.info(f"new session {sess.id} created")
        
        # 会话超时
        if time.time() - self.session_start_t >self.session_timeout:
            logger.info(f"Session {sess.id} timeout, reset.")
            self.speech.reset()
            self.dialogue_reset()

            self.speech._speak("本次对话已超时，将结束对话，如需帮助请再次唤醒我。")
            return

        sess.history.append(f"User: {user_input}")

        # 用户主动结束会话
        if is_end_session(user_input):
            logger.info(f"Session {sess.id} terminated by user.")            

            self.speech.reset()
            self.dialogue_reset()

            self.speech._speak( "好的，您已主动结束对话，如需帮助请再次唤醒我。") 
            return 
        # 用户主动下发指令“休息一下”，机器人各个模块 reset,并导航到休息点
        if is_rest(user_input):
            logger.info("收到休息指令，开始执行 reset vla → reset vln → 导航")
            # 1. 发布 VLA Reset
            # self._vla_reset_done = False
            # self._vla_reset_pub.publish()
            # self.speech._speak("正在重置 VLA 系统...")
            # if not self._wait_for_reset("_vla_reset_done"):
            #     self.speech._speak("VLA 重置失败，请检查系统。")
            #     return
            
            # 2. 发布 VLN Reset
            # vln_reset_msg = ResetVLN()
            # vln_reset_msg.reset_status = 1
            # self._vln_reset_done = False
            # self._vln_reset_pub.publish()
            # self.speech._speak("正在重置 VLN 系统...")
            # if not self._wait_for_reset("_vln_reset_done"):
            #     self.speech._speak("VLN 重置失败，请检查系统。")
            #     return

            # 3. VLN 导航到休息点
            
            return self.handle_rest()        

        # =========================
        # 根据状态处理不同意图
        # =========================
        if sess.state == "NEW":
            intent = self.intent_router.classify(user_input)
            sess.intent = intent
            logger.info(f"Session {sess.id} intent: {intent}")

            if intent == "QA":
                sess.state = "QA"
                reply = self._do_qa(user_input, sess)
                sess.history.append(f"Bot: {reply}")
                self._process_qa(reply)
                
                # return 

            elif intent == "PLAN": 
                sess.state = "PLAN"
                sess.last_clarified_command = ""  # 初始化
                
                # LLM 先判指令清晰度
                need_clarify, clar_q,clarified_cmd,final_cmd = self.clarifier.needs_clarification(
                    full_instruction=user_input,
                    history=sess.history,
                    clarify_history=sess.clarify_qs,
                    last_clarified_command=sess.last_clarified_command)
                
                sess.last_clarified_command = clarified_cmd
                print("=============================")
                print("need_clarify:",need_clarify)
                print("clar_q:",clar_q)
                print("clarified_cmd:",clarified_cmd)
                print("final_cmd:",final_cmd)

                if need_clarify:
                    sess.plan_state = "PLAN_CLARIFY"
                    sess.clarify_qs.append(clar_q)
                    sess.history.append(f"Bot: {clar_q}")
                    self.speech._speak(clar_q)
                    # return

                else:
                    if not final_cmd.strip(): 
                        logger.info(f"会话 {sess.id}， 模糊指令或者无法执行。")                       
                        self.speech.reset()
                        self.dialogue_reset()

                        self.speech._speak("我还在学习中，暂时不允许执行这样的指令，请谅解，如需帮助请再次唤醒我。")
                        # return
                    else:
                        logger.info(f"会话 {sess.id}， 指令清晰，开始执行规划。") 
                        sess.history.append(f"Bot: {final_cmd}")
                        # self._do_plann(final_cmd)

                        # self.speech.reset()
                        # self.dialogue_reset()
                        return final_cmd
            else:
                logger.info(f"会话 {sess.id} 意图识别失败。")

                self.speech.reset()
                self.dialogue_reset()

                self.speech._speak("我还在学习中，暂时不允许执行这样的指令，请谅解，如需帮助请再次唤醒我。")
                # return
        # 多轮 QA
        elif sess.state == "QA":            
            reply = self._do_qa(user_input, sess) # 多轮 QA   
            sess.history.append(f"Bot: {reply}")         
            self._process_qa(reply)
            
            # return
        # 多轮 PLAN
        elif sess.state == "PLAN":
            if sess.plan_state == "PLAN_CLARIFY":
                # 用户回答澄清问题后，组合成累积指令
                # combined = sess.history[0].replace("User: ", "") + "；补充：" + user_input
                combined_instr = sess.last_clarified_command + "；补充：" + user_input
                need_clarify, clar_q,clarified_cmd,final_cmd = self.clarifier.needs_clarification(
                    full_instruction=combined_instr,
                    history=sess.history,
                    clarify_history=sess.clarify_qs,
                    last_clarified_command=sess.last_clarified_command)
                
                sess.last_clarified_command = clarified_cmd

                if need_clarify:
                    sess.clarify_qs.append(clar_q)
                    sess.history.append(f"Bot: {clar_q}")
                    self.speech._speak(clar_q)
                    # return 
                else:         
                    # self._do_plann(final_cmd)
                    sess.history.append(f"Bot: {clar_q}")

                    # self.speech.reset()
                    # self.dialogue_reset()
                    return final_cmd
        else:
            # 已结束或未知状态，则重置
            logger.info("会话已结束。如要重新开始，请重新提问。")
        
        return None
        
    # =========================
    # QA 对话
    # =========================
    def _do_qa(self, user_input: str, sess: Session) -> str:
        # 多轮 QA 用 chat 模板，并带上历史
        history = "\n".join(sess.history)
        # return self.intent_router.llm.chat(
        #     template_key="llm_qa",
        #     query=user_input,
        #     context=history
        # )

        # for Qwen
        return self.qa_manager.answer(question=user_input,history=history)

    def _process_qa(self,reply):
        truncated, remaining = truncate_by_duration(reply, max_seconds=30, chars_per_second=4.0)        
        
        self.speech._speak(truncated) # 先播报截断部分

        # 如果有剩余内容，则询问用户是否继续播放
        if remaining:
            self.speech._speak("内容较长，我为您自动截断剩余部分。")

    
    # =========================
    # PLAN 任务执行
    # =========================
    # def _do_plann(self,reply):
    #     self.speech._speak("任务澄清完成，将要执行的任务是：" + reply)
    #     self.speech._speak("开始规划任务。")

    #     max_retries = 3
    #     parse_result = None

    #     for attempt in range(1, max_retries + 1):
    #         logger.info(f"第 {attempt} 次尝试规划任务...")
    #         parse_result = self.llm_planner.plan(reply, context="")

    #         if parse_result["error"] is None:
    #             actions = parse_result["actions"]
    #             self.speech._speak("任务规划完成，开始执行任务。")
    #             self.plans_manager.schedule(actions)
    #             break
    #         else:
    #             logger.info(f"任务规划失败，错误信息: {parse_result['error']}")
    #             if attempt < max_retries:
    #                 # tts.speak("任务规划失败，正在重试。")
    #                 # time.sleep(0.05)
    #                 continue
    #             else:
    #                 logger.info(f"经过3次尝试，任务规划失败，错误信息: {parse_result['error']}")
    #                 self.speech._speak("我还是没有理解您的意图，请重新下达指令。")
    #                 # 重置对话状态                            
    #                 self.speech.reset()
    #                 self.dialogue_reset()

    #                 return
