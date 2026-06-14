import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://127.0.0.1:8001/api/chat"

def run_simulation():
    prompt = "我想学习《随机信号分析》大纲中的章节：【平稳窄带随机过程】。请为我梳理这一章的核心研究对象、前后知识关联以及它能解决什么工程问题。"
    
    # --- FIRST CLICK ---
    payload1 = {
        "prompt": prompt,
        "signal_context": None,
        "current_node_id": "",
        "graph_node_name": "平稳窄带随机过程",
        "history": []
    }
    
    print("--- Sending First Click Request ---")
    resp1 = requests.post(API_URL, json=payload1, stream=True)
    if resp1.status_code != 200:
        print(f"Error: status code {resp1.status_code}")
        print(resp1.text)
        return
        
    first_reply_text = ""
    first_metadata = None
    
    # Process SSE stream
    for line in resp1.iter_lines():
        if not line:
            continue
        line_str = line.decode('utf-8').strip()
        if line_str.startswith("data:"):
            data_json = json.loads(line_str[5:])
            if data_json.get("type") == "text":
                first_reply_text += data_json["content"]
            elif data_json.get("type") == "metadata":
                first_metadata = data_json

    print("\n--- First Click Response Metadata Reply ---")
    print(first_metadata.get("reply") if first_metadata else first_reply_text)
    
    # --- SECOND CLICK ---
    # History format matches frontend/js/chat.js: S.chatHistory.push({ role: "user", content: textToSend }) and assistant
    history = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": first_metadata.get("reply") if first_metadata else first_reply_text}
    ]
    
    payload2 = {
        "prompt": prompt,
        "signal_context": None,
        "current_node_id": "",
        "graph_node_name": "平稳窄带随机过程",
        "history": history
    }
    
    print("\n\n--- Sending Second Click Request (with History) ---")
    resp2 = requests.post(API_URL, json=payload2, stream=True)
    if resp2.status_code != 200:
        print(f"Error: status code {resp2.status_code}")
        print(resp2.text)
        return
        
    second_reply_text = ""
    second_metadata = None
    
    for line in resp2.iter_lines():
        if not line:
            continue
        line_str = line.decode('utf-8').strip()
        if line_str.startswith("data:"):
            data_json = json.loads(line_str[5:])
            if data_json.get("type") == "text":
                second_reply_text += data_json["content"]
            elif data_json.get("type") == "metadata":
                second_metadata = data_json

    print("\n--- Second Click Response Metadata Reply ---")
    print(second_metadata.get("reply") if second_metadata else second_reply_text)

if __name__ == "__main__":
    run_simulation()
