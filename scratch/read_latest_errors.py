with open("c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/frontend_errors.log", "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"Total lines in error log: {len(lines)}")
for line in lines[-10:]:
    print(line.strip())
