import re
with open("frontend/index.html", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "id=" in line or "class=" in line:
        if any(w in line for w in ["panel", "sidebar", "chat", "knowledge", "card"]):
            print(f"{i+1}: {line.strip()}")
