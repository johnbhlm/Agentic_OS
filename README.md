
# H10-w Instruction Instruction Engineering


## 🗞️ News
- **`2025-09-17 _release`**: 🤗 [2025.09.17_release 增加 “到我这里” 指令功能，更行TTS 播报内容]
- **`2025-09-17`**: 🤗 [2025.09.17 删除开机播报功能，删除“休息一下”功能中VLA和VLN复位处理，屏蔽用户指令中“在呢，请讲”音响回声，修复已知bug]
- **`2025-09-16`**: 🤗 [2025.09.16 增加开机播报和“休息一下”功能，去掉“地面”所有操作，更新播报语，修复已知bug]
- **`2025-09-10`**: 🤗 [2025.09.10 增加玩偶颜色映射、桌子编号映射、电视柜操作，修复短指令bug]
- **`2025-09-09`**: 🤗 [2025.09.09 增加"给我“等指令，修复“去”简单指令和需要澄清确认起始点bug]
- **`2025-09-08`**: 🤗 [2025.09.08 展会稳定版]
- **`2025-09-07`**: 🤗 [2025.09.07 展会稳定版]

## 📆 Todo
- [x] 优化指令堆叠问题
- [x] 优化调用大模型相应速度

## ⭐️ Features
**指令工程支持功能：**

1. 支持QA [暂时不能联网]

2. 模糊指令多轮澄清: 基于 LLM 判断模糊指令缺失信息，并针对性的提问澄清

3. 指令规划：基于 LLM 生成 action list

4. 语音交互：KWS、ASR、TTS


## 🛠️ Setup and Install
1. Switch microphone input device:
```bash
pactl list short sources
pactl set-default-source alsa_input.usb-Shenzhen_Hollyland_Technology_Co._Ltd_Wireless_Microphone_Wireless_Microphone-01.analog-stereo
```

2. Configuration Environment
```bash
# clone repo.
git clone https://git.agile-robots.com/bao.he/h10_w_instruction.git


# build conda env.
conda create -n ass_robot python==3.10
conda activate ass_robot
pip install -r requirements.txt
```


## 💡 Usage

### 1. 启动代理

```sh
clash
```
### 1. 启动程序
```sh
cd ~/Code/assistant_ws_v2
./run_ass_robot.sh
```

## Result

