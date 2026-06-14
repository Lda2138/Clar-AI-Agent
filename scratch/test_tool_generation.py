import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_brain import SignalAgent
from backend.parser import extract_reply_robust

agent = SignalAgent()
prompt = "请帮我生成一个频率为200Hz的正弦信号，采样率为10000Hz"

stream = agent.chat_stream(prompt, None, None, history=[], require_json=True)
raw_chunks = []
for chunk in stream:
    raw_chunks.append(chunk)

full_raw = "".join(raw_chunks)
extracted = extract_reply_robust(full_raw)

with open("scratch/test_out.json", "w", encoding="utf-8") as f:
    json.dump(extracted, f, ensure_ascii=False, indent=2)

print("Saved output to scratch/test_out.json")
