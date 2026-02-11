import logging
from assistant_robot.common.utils import load_yaml,init_logging,truncate_by_duration
# init_logging(level=logging.DEBUG, log_file="logs/app.log",enable=True)
# init_logging(level=logging.DEBUG, log_file=None, enable=False)

import sys
import rclpy
import logging
import sounddevice as sd
import numpy as np
import threading
from assistant_robot.common.gpt_client.factory import ProviderFactory

from assistant_robot.interaction.KWS.kws_openWakeWord import OpenWakeWordKWS
from assistant_robot.interaction.ASR.funasr_transcriber import FunASRTranscriber
from assistant_robot.interaction.TTS.tts_kokoro import KokoroTTS
from assistant_robot.interaction.speech_manager import SpeechManager
from assistant_robot.interaction.Dialogue.dialogue_manager import DialogueManager
from assistant_robot.planner.llm_based.llm_planner import LLM_Planner
from assistant_robot.planner.plans_manager import PlansManager

# from assistant_robot_msgs.msg import VLNStatus,VLAStatus
# from assistant_robot.memory.ros_interface import VLA_StatusSubscriber, VLN_StatusSubscriber

import time

logger = logging.getLogger(__name__)

# system_state = {"vla_ready": False, "vln_ready": False}

# def vla_on_status(msg: VLAStatus):
#     # logger.info(f"接收到 VLA 状态: {msg.status}")
#     system_state["vla_ready"] = (msg.status == 1)

# def vln_on_status(msg: VLNStatus):
#     # logger.info(f"接收到 VLN 状态: {msg.status}")
#     system_state["vln_ready"] = (msg.status == 1)


# def wait_for_ready(node, tts,timeout=300):
#     wait_start = time.time()
#     while rclpy.ok():
#         rclpy.spin_once(node, timeout_sec=0.1)
#         # if system_state["vla_ready"] and system_state["vln_ready"]:
#         #     tts.speak("所有状态已就绪，现在开始工作。")
#         #     return True
#         if system_state["vln_ready"]:
#             tts.speak("导航程序状态已就绪，现在开始工作。")
#             return True
#         if time.time() - wait_start > timeout:
#             tts.speak("系统初始化超时，请检查导航和操作程序。")
#             return False
#         time.sleep(0.5)


def kws_loop(speech_manager):
    kws_engine = OpenWakeWordKWS()
    rate = 16000
    frame_length_ms = 80
    blocksize = int(rate * frame_length_ms / 1000)

    def audio_callback(indata, frames, time_info, status):
        audio = np.frombuffer(indata, dtype=np.int16).flatten()
        detected, score = kws_engine.detect(audio)
        if detected:
            print(f"[KWS] 唤醒成功 (score={score:.2f})")
            speech_manager.wake_event.set()   # 通知 SpeechManager

    stream = sd.InputStream(samplerate=rate, channels=1, dtype="int16",
                            blocksize=blocksize, callback=audio_callback)
    with stream:
        while True:
            sd.sleep(1000)  # 保持监听

def do_plan(reply,tts,llm_planner,plans_manager):
    # tts.speak("任务澄清完成，将要执行的任务是：" + reply)
    print(f"任务澄清完成，将要执行的任务是：" + reply)
    # tts.speak("开始规划任务。")
    if "休息一下" not in reply:
        max_retries = 3
        parse_result = None

        for attempt in range(1, max_retries + 1):
            logger.info(f"第 {attempt} 次尝试规划任务...")
            parse_result = llm_planner.plan(reply, context="")

            if parse_result["error"] is None:
                actions = parse_result["actions"]
                # print(actions)
                tts.speak("好的，开始执行任务。")
                plans_manager.schedule(actions)
                break
            else:
                logger.info(f"任务规划失败，错误信息: {parse_result['error']}")
                if attempt < max_retries:
                    # tts.speak("任务规划失败，正在重试。")
                    # time.sleep(0.05)
                    continue
                else:
                    logger.info(f"经过3次尝试，任务规划失败，错误信息: {parse_result['error']}")
                    tts.speak("我还在学习中，暂时不允许执行这样的指令，请谅解，如需帮助请再次唤醒我。")
    else:
        actions=[" go-to current-location init"]
        # print(actions)
        plans_manager.schedule(actions)
        tts.speak( "我要休息了，如有需要请再次唤醒我。")  
    return


def main(): 
    init_logging()

    logger.info("****** Start Assistant Robot: Instruction Engineering ****** ")
    # ****** 1. ROS2 init ******
    rclpy.init()
    node = rclpy.create_node('assistant_robot')

    # ****** 2. LLM init ******
    gpt_cfg = load_yaml("gpt_config.yaml")
    gpt_client = ProviderFactory.create(gpt_cfg)    

    llm_planner = LLM_Planner(gpt_client=gpt_client)
    # ****** 3. ASR  & TTS  & speech init ******        
    # transcriber = FunASRTranscriber(model_name="paraformer-zh",vad_model="fsmn-vad",punc_model="ct-punc",device="cuda:0", hotword="小爱同学")
    transcriber = FunASRTranscriber(model_name="paraformer-zh",vad_model="fsmn-vad",punc_model="ct-punc",device="cuda:0")
    tts = KokoroTTS() 
    speech = SpeechManager(transcriber=transcriber,tts=tts,kws="ni hao si ling")   
    
    # ****** TTS 播报所有程序就绪状态 ****** 
    # 创建订阅
    # vla_status_sub = VLA_StatusSubscriber(node, vla_on_status)
    # vln_status_sub = VLN_StatusSubscriber(node, vln_on_status)

    # ===== 等待 VLA & VLN 就绪 =====
    # wait_for_ready(node, tts)
    
    # ****** 4. Dialogue init ******   
    dlg = DialogueManager(gpt_client,speech_mannger=speech,node=node) 
    session_id = None  # 会话 ID，用于多轮对话,场景：当语音转成文本后，交给 DialogueManager 处理

    plans_manager = PlansManager(node=node, tts=tts)
    def handle_command(text: str):
        nonlocal session_id
        
        final_cmd = dlg.handle(text, session_id) # 交给 DialogueManager 处理，得到新的 session_id 和回复
        
        if final_cmd is not None:
            do_plan(final_cmd,tts,llm_planner,plans_manager)
            speech.reset()
            dlg.dialogue_reset()
                
    # ****** 5. 启动语音监听 ****** 
    speech.set_transcription_callback(handle_command)
    speech.start()

    kws_thread = threading.Thread(target=kws_loop, args=(speech,), daemon=True)
    kws_thread.start()

    # ****** 5. 保持节点运行 ****** 
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()

