# coding: utf-8
import os

found = False
for root, dirs, files in os.walk('c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/frontend'):
    for file in files:
        if file.endswith('.html') or file.endswith('.js'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if '核心知识点' in line:
                        print(f"{filepath}:{i+1}: {line.strip()}")
                        found = True
if not found:
    print("Not found anywhere in frontend.")
