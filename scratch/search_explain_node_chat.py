with open("c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/frontend/js/chat.js", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx, line in enumerate(lines):
    if "explainNode" in line:
        print(f"Line {idx+1}: {line.strip()}")
