import urllib.request
import json
import sys

# Reconfigure stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def test_chat_live():
    url = "http://127.0.0.1:8001/api/chat"
    payload = {
        "prompt": "请讲解平稳窄带随机过程的定义，我想看它的公式推导并切换到知识图谱页",
        "signal_context": {},
        "current_node_id": "",
        "graph_node_name": "",
        "history": []
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    
    print("Sending request to live server /api/chat...")
    try:
        with urllib.request.urlopen(req) as response:
            buffer = ""
            for chunk in response:
                decoded = chunk.decode('utf-8')
                buffer += decoded
                lines = decoded.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith("data:"):
                        try:
                            msg = json.loads(line[5:])
                            if msg.get("type") == "text":
                                print(msg.get("content"), end="", flush=True)
                            elif msg.get("type") == "metadata":
                                print("\n\n--- METADATA RECEIVED ---")
                                print(json.dumps(msg, ensure_ascii=False, indent=2))
                        except Exception:
                            pass
    except Exception as e:
        print("\nRequest failed:", e)

if __name__ == "__main__":
    test_chat_live()
