import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
log_path = r"C:\Users\Lda001\.gemini\antigravity\brain\e7744f6e-c162-4cdb-a5e0-2f885cc72451\.system_generated\logs\transcript.jsonl"

if not os.path.exists(log_path):
    print("Log path not found")
    sys.exit(1)

with open(log_path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if 2500 <= idx <= 2829:
            try:
                obj = json.loads(line)
                print(f"Step {idx} | Type: {obj.get('type')} | Source: {obj.get('source')}")
                content = obj.get("content", "")
                print(f"Content: {content[:400]}")
                print("-" * 50)
            except Exception:
                pass
