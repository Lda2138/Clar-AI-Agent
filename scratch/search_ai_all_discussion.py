import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Lda001\.gemini\antigravity\brain\e7744f6e-c162-4cdb-a5e0-2f885cc72451\.system_generated\logs\transcript.jsonl"
if not os.path.exists(log_path):
    print("Log not found")
    sys.exit(1)

with open(log_path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        try:
            obj = json.loads(line)
            content = obj.get("content", "")
            # Check model responses after step 822
            if idx > 822 and obj.get("source") == "MODEL" and obj.get("type") == "PLANNER_RESPONSE":
                if any(k in content for k in ["AI-all", "all", "渲染", "之前", "历史", "图像"]):
                    print(f"=== STEP {idx} (type: {obj.get('type')}) ===")
                    print(content[:1200])
                    print("="*60)
        except Exception:
            pass
