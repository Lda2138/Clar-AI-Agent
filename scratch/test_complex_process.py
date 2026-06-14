import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_brain import SignalAgent

agent = SignalAgent()
prompt = "请帮我深入剖析核心知识点：【复过程与复包络】。希望包含它的数学公式定义、物理含义、以及我们在做系统实验或仿真时需要注意的常见误区。"

stream = agent.chat_stream(prompt, None, None, history=[], require_json=True)
raw_chunks = []

for chunk in stream:
    raw_chunks.append(chunk)

full_raw = "".join(raw_chunks)
print("RAW LENGTH:", len(full_raw))
print("RAW START:")
print(repr(full_raw[:300]))
print("RAW END:")
print(repr(full_raw[-300:]))

# Also test parsing
from backend.parser import extract_reply_robust
extracted = extract_reply_robust(full_raw)
print("EXTRACTED SUGGESTED PAGE:", extracted.get("suggested_page"))
print("EXTRACTED REPLY LENGTH:", len(extracted.get("reply") or ""))
