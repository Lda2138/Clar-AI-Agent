import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
log_path = r"C:\Users\Lda001\.gemini\antigravity\brain\e7744f6e-c162-4cdb-a5e0-2f885cc72451\.system_generated\logs\transcript.jsonl"
out_path = r"c:\Users\Lda001\Desktop\the-agent\agent-by-DZLiu\scratch\output_step_2500.txt"

if not os.path.exists(log_path):
    print("Log path not found")
    sys.exit(1)

with open(log_path, 'r', encoding='utf-8') as f, open(out_path, 'w', encoding='utf-8') as fout:
    for idx, line in enumerate(f):
        if 2500 <= idx <= 2522:
            try:
                obj = json.loads(line)
                stype = obj.get("type")
                source = obj.get("source")
                content = obj.get("content", "")
                if stype in ["PLANNER_RESPONSE", "MODEL_RESPONSE", "USER_INPUT"] or source == "MODEL":
                    fout.write(f"Step {idx} | Type: {stype} | Source: {source}\n")
                    fout.write(f"Content:\n{content}\n")
                    fout.write("=" * 60 + "\n")
            except Exception as e:
                fout.write(f"Error parsing line {idx}: {e}\n")
print("Done writing to output_step_2500.txt")
