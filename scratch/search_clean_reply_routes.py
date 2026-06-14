with open("c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/backend/chat_routes.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx, line in enumerate(lines):
    if "_clean_reply" in line:
        print(f"Line {idx+1}: {line.strip()}")
