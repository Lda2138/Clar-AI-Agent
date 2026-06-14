import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_brain import SignalAgent
from backend.parser import JSONReplyStreamParser, extract_reply_robust

sys.stdout.reconfigure(encoding='utf-8')

def test():
    agent = SignalAgent()
    
    first_reply = (
        "好的，我们来梳理平稳窄带随机过程的核心研究对象、前后知识关联以及它能解决什么工程问题。\n\n"
        "**1. 核心研究对象**\n"
        "平稳窄带随机过程的功率谱密度集中在某个高频 $\\omega_0$ 附近的窄带内。可用莱斯表示法分解为：\n"
        "$$X(t) = X_c(t)\\cos(\\omega_0 t) - X_s(t)\\sin(\\omega_0 t)$$\n"
        "其中，$X_c(t)$ 和 $X_s(t)$ 是低频同相和正交分量，且满足：\n"
        "$$E[X_c(t)] = E[X_s(t)] = 0$$\n"
        "$$R_{X_c}(\\tau) = R_{X_s}(\\tau), R_{X_c X_s}(\\tau) = -R_{X_s X_c}(\\tau)$$\n"
        "### 前后知识关联\n"
        "- **前置知识**: 广义平稳过程(WSS)。\n"
        "[NODE:KP_CH3_01]"
    )
    
    history = [
        {"role": "user", "content": "我想学习《随机信号分析》大纲中的章节：【平稳窄带随机过程】。请为我梳理这一章的核心研究对象、前后知识关联以及它能解决什么工程问题。"},
        {"role": "assistant", "content": first_reply}
    ]
    
    prompt = "我想学习《随机信号分析》大纲中的章节：【平稳窄带随机过程】。请为我梳理这一章的核心研究对象、前后知识关联以及它能解决什么工程问题。"
    
    for i in range(5):
        print(f"\n===== RUN {i+1} =====")
        stream = agent.chat_stream(prompt, None, None, history=history, require_json=True)
        raw_chunks = []
        for chunk in stream:
            if not chunk.startswith("[STATUS]: "):
                raw_chunks.append(chunk)
        full_raw = "".join(raw_chunks)
        extracted = extract_reply_robust(full_raw)
        reply = extracted.get("reply") or ""
        print(f"Reply starts with: {repr(reply[:150])}...")

if __name__ == "__main__":
    test()
