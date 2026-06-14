import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "ai-panel" in line or "Clar" in line:
        if i < 800: # styles usually, skip
            continue
        print(f"Line {i+1}: {line.strip()}")
        for j in range(max(0, i-4), min(len(lines), i+8)):
            print(f"  [{j+1}] {lines[j].rstrip()}")
        print("-" * 50)
