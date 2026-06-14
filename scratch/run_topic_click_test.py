import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_brain import SignalAgent
from backend.parser import JSONReplyStreamParser, extract_reply_robust

# Simulating topic click for '平稳随机过程' which corresponds to KP_CH1_03
prompt = "请帮我深入剖析核心知识点：【平稳随机过程】。希望包含它的数学公式定义、物理含义、以及我们在做系统实验或仿真时需要注意的常见误区。"

payload = {
    "prompt": prompt,
    "signal_context": None,
    "current_node_id": "KP_CH1_03",
    "graph_node_name": "平稳随机过程",
    "history": []
}

agent = SignalAgent()
print("Calling agent.chat_stream for Topic Click...")
stream = agent.chat_stream(prompt, None, {"current_node_id": "KP_CH1_03", "graph_node_name": "平稳随机过程"}, history=[], require_json=True)

parser = JSONReplyStreamParser()
raw_chunks = []
parsed_output = []

for chunk in stream:
    raw_chunks.append(chunk)
    chars = list(parser.feed(chunk))
    if chars:
        char_str = "".join(chars)
        parsed_output.append(char_str)
        print(char_str, end="", flush=True)

full_raw = "".join(raw_chunks)
print("\n\n--- Raw Response ---")
print(full_raw)
