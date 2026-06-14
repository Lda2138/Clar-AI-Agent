import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
log_path = r"C:\Users\Lda001\.gemini\antigravity\brain\e7744f6e-c162-4cdb-a5e0-2f885cc72451\.system_generated\logs\transcript.jsonl"

if not os.path.exists(log_path):
    print("Log path not found")
    sys.exit(1)

keywords = ["吃了", "被吃", "前半", "渲染", "错误", "连续点击", "第一次"]

with open(log_path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        try:
            obj = json.loads(line)
            content = obj.get("content", "")
            if any(kw in content for kw in keywords):
                print(f"Step {idx} | Type: {obj.get('type')} | Source: {obj.get('source')}")
                print(f"Content: {content[:300]}")
                print("-" * 50)
        except Exception:
            pass
