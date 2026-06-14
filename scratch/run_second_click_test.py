import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_brain import SignalAgent
from backend.parser import JSONReplyStreamParser, extract_reply_robust

# Force stdout to use utf-8
sys.stdout.reconfigure(encoding='utf-8')

def test():
    agent = SignalAgent()
    
    # 1. Simulate a realistic first turn reply
    first_reply = (
        "平稳窄带随机过程是随机信号分析中的核心概念。它的数学表示为：\n"
        "$$X(t) = X_c(t)\\cos(\\omega_0 t) - X_s(t)\\sin(\\omega_0 t)$$\n"
        "其中，$X_c(t)$ 和 $X_s(t)$ 是低频同相和正交分量，且它们满足：\n"
        "$$E[X_c(t)] = E[X_s(t)] = 0$$\n"
        "$$R_{X_c}(\\tau) = R_{X_s}(\\tau), R_{X_c X_s}(\\tau) = -R_{X_s X_c}(\\tau)$$\n"
        "### 前后知识关联\n"
        "- **前置知识**: 广义平稳过程(WSS)。\n"
        "[NODE:KP_CH3_01]"
    )
    
    # History containing the first turn
    history = [
        {"role": "user", "content": "我想学习《随机信号分析》大纲中的章节：【平稳窄带随机过程】。请为我梳理这一章的核心研究对象、前后知识关联以及它能解决什么工程问题。"},
        {"role": "assistant", "content": first_reply}
    ]
    
    # Second turn prompt (clicking the same node again)
    prompt = "我想学习《随机信号分析》大纲中的章节：【平稳窄带随机过程】。请为我梳理这一章的核心研究对象、前后知识关联以及它能解决什么工程问题。"
    
    print("Sending request to agent.chat_stream for the second turn...")
    stream = agent.chat_stream(prompt, None, None, history=history, require_json=True)
    
    parser = JSONReplyStreamParser()
    raw_chunks = []
    parsed_output = []
    
    print("\n--- Stream chunks ---")
    for chunk in stream:
        raw_chunks.append(chunk)
        parsed_chars = list(parser.feed(chunk))
        if parsed_chars:
            char_str = "".join(parsed_chars)
            parsed_output.append(char_str)
            print(f"RAW: {repr(chunk)} -> PARSED: {repr(char_str)}")
            
    full_raw = "".join(raw_chunks)
    full_parsed = "".join(parsed_output)
    
    print("\n--- Final Summary ---")
    print(f"Full Raw length: {len(full_raw)}")
    print(f"Full Raw Sample: {full_raw[:300]} ...")
    print("\n--- Full Parsed Output ---")
    print(full_parsed)
    
    print("\n--- Extract Reply Robust Output ---")
    extracted = extract_reply_robust(full_raw)
    print(json.dumps(extracted, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test()
