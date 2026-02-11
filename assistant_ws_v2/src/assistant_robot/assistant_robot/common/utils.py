import logging
import os
import yaml
from pypinyin import pinyin, Style
import re


from ament_index_python.packages import get_package_share_directory

def load_yaml(name: str) -> dict:
    """
    加载 ROS2 包安装目录下 share/assistant_robot/config/ 的 YAML 文件。
    调用时直接传入文件名（不带路径）。
    """
    package_share_dir = get_package_share_directory('assistant_robot')
    cfg_path = os.path.join(package_share_dir, 'config', name)
    with open(cfg_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
    
def load_yaml_test(name: str) -> dict:
    """
    加载项目根目录下 config/ 里的 YAML 文件。
    调用时直接传入文件名（不带路径）。
只适合在 源码树 下运行，因为它是通过 __file__ 逆推两级目录找到 project_root，然后拼 config/xxx.yaml。
但是 colcon build 安装到 install/assistant_robot/lib/python3.10/site-packages 后，这个逻辑会失效，因为项目已经被拷贝/软链接到 site-packages，上两级目录不再是你的源码根目录。
    """
    base = os.path.dirname(__file__)            # common/ 目录
    project_root = os.path.abspath(os.path.join(base, "..", ".."))  # 或用更稳的方式获取根
    cfg_path = os.path.join(project_root, "config", name)
    with open(cfg_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def init_logging(level: int = logging.INFO, log_file: str = None,enable: bool = True):
    """
    初始化全局日志器：
      - 输出到控制台
      - 可选输出到文件
      - 格式：[时间] 模块名 日志级别: 消息

    :param level: 日志级别，例如 logging.INFO、logging.DEBUG
    :param log_file: 如果不为 None，则同时将日志写入该文件
    """

    root_logger = logging.getLogger()

    # 清除所有已有 handlers，确保干净状态
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    if not enable:
        root_logger.setLevel(logging.CRITICAL + 1) # 方法 1：设置日志级别为极高      
        root_logger.addHandler(logging.NullHandler())  # 方法 2：添加 NullHandler，防止 fallback 到 stderr
        # 方法 3：移除所有子 logger 的 handler（彻底干净）
        for name in logging.root.manager.loggerDict:
            logging.getLogger(name).handlers.clear()
        return
    
    root_logger.setLevel(level)

    formatter = logging.Formatter("[%(asctime)s] %(name)s %(levelname)s: %(message)s")

    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件 handler（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def convert_to_pinyin(chinese_str):
    chars = re.findall(r'[\u4e00-\u9fa5]', chinese_str)
    pinyin_result = pinyin("".join(chars), style=Style.NORMAL)
    
    return ' '.join([item[0] for item in pinyin_result])

def is_end_session(input: str) -> bool:
    # 结束对话的简单触发词
    # END_TOKENS = {"再见", "拜拜", "结束", "谢谢", "thank you", "bye"}
    END_TOKENS = {"结束会话", "结束对话", "结束绘画", "结束回话","结束"}
    
    return any(tok in input.strip().lower() for tok in END_TOKENS)

def truncate_by_duration(text: str, max_seconds: int = 15, chars_per_second: float = 4.0):
    """
    截断文本以控制播报时长
    :param text: 原始文本
    :param max_seconds: 最大播报时长（秒）
    :param chars_per_second: 平均语速（汉字数/秒）
    :return: (truncated_text, remaining_text)
    """
    max_chars = int(max_seconds * chars_per_second)
    if len(text) > max_chars:
        return text[:max_chars], text[max_chars:]
    return text, ""


def is_rest(input: str) -> bool:
    # 结束对话的简单触发词
    REST_TOKENS = {"休息一下", "休息一下吧", "休息吧"}
    
    return any(tok in input.strip().lower() for tok in REST_TOKENS)