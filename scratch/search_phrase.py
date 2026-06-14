import os

search_phrase = "agent_brain_step571"
for root, dirs, files in os.walk("c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu"):
    for file in files:
        if file.endswith(('.py', '.js', '.html')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if search_phrase in line:
                            print(f"Found in {path} at line {line_num}: {line.strip()}")
            except Exception:
                pass
