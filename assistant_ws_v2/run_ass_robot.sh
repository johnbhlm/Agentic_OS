#!/bin/bash
source ~/.bashrc
# === 1. 初始化 conda ===
source /home/maintenance/miniforge3/etc/profile.d/conda.sh
conda activate ass-robot-qwen

# source /home/diana/miniforge3/etc/profile.d/conda.sh
# conda activate ass_robot
# === 2. 设置代理（可选）===
export http_proxy='http://127.0.0.1:7890'
export https_proxy='http://127.0.0.1:7890'

# === 3. 进入工作空间 ===
cd ~/Code/instruction/assistant_ws_v2
# cd ~/Code/assistant_ws_v2

# === 4. 加载 ROS2 环境 ===
source /opt/ros/humble/setup.bash

# === 5. 编译项目 ===
colcon build --packages-select assistant_robot_msgs assistant_robot

# === 6. 加载构建结果 ===
source install/setup.bash

# === 7. 运行节点 ===
ros2 run assistant_robot main #2>/dev/null
