import sys
import json
import os

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Lda001\.gemini\antigravity\brain\e7744f6e-c162-4cdb-a5e0-2f885cc72451\.system_generated\logs\transcript.jsonl"

if not os.path.exists(log_path):
    print(f"Log path does not exist: {log_path}")
    sys.exit(1)

print("Reading transcript logs...")
with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total steps in transcript: {len(lines)}")

# Let's search backwards for user prompt containing "平稳随机过程"
for idx in range(len(lines) - 1, -1, -1):
    try:
        step = json.loads(lines[idx])
        content = step.get("content", "")
        # Print steps related to our query
        if "平稳随机过程" in content or "WSS" in content or "F_{X" in content:
            print(f"\n--- STEP INDEX {step.get('step_index', idx)} (Type: {step.get('type')}, Source: {step.get('source')}) ---")
            print("Content:")
            print(content)
            # If there are tool calls or other fields
            if "tool_calls" in step:
                print("Tool calls:", json.dumps(step["tool_calls"], ensure_ascii=False))
    except Exception as e:
        print(f"Error parsing line {idx}: {e}")
