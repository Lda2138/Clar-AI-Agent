import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

html_path = 'frontend/index.html'
if not os.path.exists(html_path):
    print("HTML path not found")
    exit(1)

content = open(html_path, encoding='utf-8').read().splitlines()
idx = -1
for i, l in enumerate(content):
    if 'id="ai-panel"' in l or "id='ai-panel'" in l:
        idx = i
        break

if idx != -1:
    print(f"Found ai-panel at line {idx+1}")
    for i in range(max(0, idx-10), min(len(content), idx+40)):
        print(f"{i+1}: {content[i]}")
else:
    print("ai-panel not found")
