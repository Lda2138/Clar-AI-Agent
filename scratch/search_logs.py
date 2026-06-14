import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

search_phrase = "平稳窄带随机过程"

paths_to_search = [
    "c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu",
    r"C:\Users\Lda001\.gemini\antigravity\brain\e7744f6e-c162-4cdb-a5e0-2f885cc72451"
]

for base_path in paths_to_search:
    if not os.path.exists(base_path):
        continue
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.log') or file.endswith('.jsonl') or file.endswith('.json'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if search_phrase in line:
                                print(f"Found in {path} at line {line_num}: {line[:200]}...")
                except Exception:
                    pass
