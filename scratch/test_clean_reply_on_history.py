import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_brain import _clean_reply

assistant_reply = (
    "【平稳窄带随机过程】是《随机信号分析》中连接基础理论与实际应用的关键章节。它的核心研究对象是**窄带随机过程**——即功率谱密度集中在某个中心频率 $f_0$ 附近、带宽 $B \\ll f_0$ 的平稳随机过程。典型例子包括通信中的调制信号、雷达回波、机械振动信号等。\n\n"
    "**前后知识关联：**\n"
    "- **前置知识：** 广义平稳过程（WSS）和功率谱密度（PSD）是基础，窄带过程是WSS的一种特例；维纳-欣钦定理用于计算其自相关函数与PSD的傅里叶变换对。\n"
    "- **后续应用：** 窄带过程的分析直接服务于通信系统中的带通信号处理、雷达目标检测、振动分析中的包络提取等。\n\n"
    "**工程问题解决：**\n"
    "1. **包络与相位分析：** 窄带过程可表示为 $X(t) = A(t)\\cos[2\\pi f_0 t + \\Phi(t)]$，其中 $A(t)$ 是慢变包络、$\\Phi(t)$ 是慢变相位。工程中常通过希尔伯特变换提取包络（如调幅信号解调）。\n"
    "2. **窄带噪声建模：** 接收机中的带通白噪声可建模为窄带过程，其同相分量 and 正交分量是相互独立（或正交）的低通过程，便于分析信噪比和误码率。\n"
    "3. **随机信号通过窄带系统：** 当宽带噪声通过窄带滤波器时，输出即为窄带过程，其统计特性（如瑞利分布包络）用于雷达恒虚警检测。\n\n"
    "若你想深入，我们可以从窄带过程的解析表示（复包络）开始推导，或直接生成一个窄带随机信号观察其时域波形和功率谱。"
)

cleaned = _clean_reply(assistant_reply)
print("--- Cleaned Reply ---")
print(cleaned)

if cleaned == assistant_reply.strip():
    print("\nSUCCESS: Cleaned reply matches original reply exactly!")
else:
    print("\nWARNING: Cleaned reply differs!")
    print("Original len:", len(assistant_reply.strip()))
    print("Cleaned len:", len(cleaned))
