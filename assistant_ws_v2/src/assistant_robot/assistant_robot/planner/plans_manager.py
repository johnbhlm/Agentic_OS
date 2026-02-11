import logging
import rclpy
from rclpy.node import Node
import time
from queue import Queue

from std_msgs.msg import String
from assistant_robot_msgs.msg import ActionStatus
from assistant_robot.memory.ros_interface import VLAPublisher, VLNPublisher, StatusSubscriber
# from assistant_ws2.src.assistant_robot.assistant_robot.memory.ros_interface import VLAPublisher, VLNPublisher, StatusSubscriber

logger = logging.getLogger(__name__)

class PlansManager:
    def __init__(self, node, tts):
        """
        :param node: rclpy.Node 用于创建话题
        :param speech_manager: 具有 speak(text:str) 方法的 TTS 播报器
        """
        self._tts = tts
        self._actions = []
        self._idx = 0
        self._executing = False
        self._action_tpye = None

        # ROS 接口
        self._vln_pub = VLNPublisher(node)
        self._vla_pub = VLAPublisher(node)        
        self._status_sub = StatusSubscriber(node, self._on_status)


    def schedule(self, actions: list[str]):
        """启动一组新的动作列表调度。"""
        if not actions:
            # self._tts.speak("没有可执行的动作")
            return
        self._actions = actions
        self._idx = 0
        self._executing = True
        self._execute_current()

    def _execute_current(self):
        """发布当前动作并播报。"""
        action = self._actions[self._idx]
        # if "init" not in action:
            # self._tts.speak(f"开始执行第{self._idx+1}步。")
        # self._tts.speak(f"{action}")
        # print(action.lower().split())
        keyword = action.lower().split()[0]

        if keyword in ('go','move','navigate','go-to'):
            logger.info("调用VLN")
            self._action_tpye = "VLN"
            self._vln_pub.publish(action, self._idx)
        
        else:
            logger.info("调用VLA")
            self._action_tpye = "VLA"
            self._vla_pub.publish(action, self._idx)

    def _on_status(self, msg: ActionStatus):
        """收到执行反馈后的回调，包含完整的重试/跳过逻辑。"""
        if not self._executing or msg.action_id != self._idx:
            return

        if self._idx < 0 or self._idx >= len(self._actions):
            logger.info(f"第{self._idx+1}步,当前动作索引越界，取消执行")
            self._executing = False
            return
        if self._action_tpye == "VLN":
            if msg.status_id==0: #成功
                logger.info(f"第{self._idx+1}步执行成功。")
                self._idx += 1
                if self._idx < len(self._actions):
                    self._execute_current()
                else:
                    if "init" not in self._actions[self._idx-1]:
                        self._tts.speak("所有动作已执行完毕，如需帮助请再次唤醒我。")
                    self._executing = False
                return
            else:
                if msg.status_id==1: #查询失败
                    logger.info(f"第{self._idx+1}步导航查询失败，取消后续执行。")
                    self._tts.speak(f"我没有找到您想要的东西，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==2: #规划失败
                    logger.info(f"第{self._idx+1}步导航规划失败，取消后续执行。")
                    self._tts.speak(f"我到不了您想去的地方，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==3: #二次规划失败
                    logger.info(f"第{self._idx+1}步导航二次确认失败，取消后续执行。")
                    self._tts.speak(f"我到不了您想去的地方，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==4: #其他未知错误
                    logger.info(f"第{self._idx+1}步导航其他原因失败，取消后续执行。")
                    self._tts.speak(f"我努力了，但是我还是到不了，取消后续执行，如需帮助请再次唤醒我。")

                self._executing = False
                return 
        elif self._action_tpye == "VLA":
            if msg.status_id==0: #成功
                logger.info(f"第{self._idx+1}步执行成功。")
                self._idx += 1
                if self._idx < len(self._actions):
                    self._execute_current()
                else:
                    self._tts.speak("所有动作已执行完毕，如需帮助请再次唤醒我。")
                    self._executing = False
                return
            else:
                if msg.status_id==1: #获取图像失败
                    # logger.info(f"第{self._idx+1}步操作中获取图像失败，取消后续执行。")
                    self._tts.speak(f"我没有找到您想要的东西，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==2: #初定位失败
                    # logger.info(f"第{self._idx+1}步操作中初定位失败，取消后续执行。")
                    self._tts.speak(f"我没有找到您想要的东西，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==3: #第一次规划失败
                    # logger.info(f"第{self._idx+1}步操作中第一次规划失败，取消后续执行。")
                    self._tts.speak(f"我无法拿到您想要的东西，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==4: #腕部相机定位失败
                    # logger.info(f"第{self._idx+1}步操作中腕部相机定位失败，取消后续执行。")
                    self._tts.speak(f"我没有找到您要的东西，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==5: #第二次规划(Pick规划)失败
                    # logger.info(f"第{self._idx+1}步操作中抓取第二次规划失败，取消后续执行。")
                    self._tts.speak(f"我无法拿到您想要的东西，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==6: #基于视觉反馈操作失败
                    logger.info(f"第{self._idx+1}步操作中基于视觉反馈操作失败，取消后续执行。")
                    # self._tts.speak(f"操作中基于视觉反馈操作失败，取消后续执行。")
                elif msg.status_id==7: #放置定位失败
                    # logger.info(f"第{self._idx+1}步操作中放置定位失败，取消后续执行。")
                    self._tts.speak(f"我不能放置到指定地点，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==8: #放置规划失败
                    # logger.info(f"第{self._idx+1}步操作中放置规划失败，取消后续执行。")
                    self._tts.speak(f"我不能放置到指定地点，取消后续执行，如需帮助请再次唤醒我。")
                elif msg.status_id==9: #抓取最终失败
                    # logger.info(f"第{self._idx+1}步操作中抓取最终失败，取消后续执行。")
                    self._tts.speak(f"我没有拿到您想要的东西，取消后续执行，如需帮助请再次唤醒我。")

                self._executing = False
                return 

        else:
            # self._tts.speak(f"第{self._idx+1}步执行失败，取消后续执行。")
            self._executing = False
            return 