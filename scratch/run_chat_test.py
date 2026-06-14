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
    prompt = "请帮我深入剖析核心知识点：【平稳随机过程】。希望包含它的数学公式定义、物理含义、以及我们在做系统实验或仿真时需要注意的常见误区。"
    
    print("Sending request to agent.chat_stream...")
    stream = agent.chat_stream(prompt, None, None, history=[], require_json=True)
    
    parser = JSONReplyStreamParser()
    raw_chunks = []
    parsed_output = []
    
    print("\n--- Raw and Parsed stream chunks ---")
    for chunk in stream:
        raw_chunks.append(chunk)
        # Parse chunk
        parsed_chars = list(parser.feed(chunk))
        if parsed_chars:
            char_str = "".join(parsed_chars)
            parsed_output.append(char_str)
            print(f"RAW CHUNK: {repr(chunk)} -> PARSED: {repr(char_str)}")
            
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
