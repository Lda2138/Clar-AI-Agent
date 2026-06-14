with open("c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/frontend/js/charts.js", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx, line in enumerate(lines):
    if "深入剖析核心知识点" in line:
        print(f"Line {idx+1}: {line.strip()}")
        # print 10 lines before and after
        start = max(0, idx - 15)
        end = min(len(lines), idx + 20)
        for i in range(start, end):
            print(f"{i+1:3d}: {lines[i]}", end="")
