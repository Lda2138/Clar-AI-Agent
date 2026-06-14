# coding: utf-8
import os
import re

js_dir = 'c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/frontend/js'
legend_pattern = re.compile(r"legend:\s*\[\{\s*data:\s*\['章节',\s*'小节',\s*'核心知识点'\],\s*textStyle:\s*\{[^}]+\},\s*bottom:\s*\d+\s*\}\],?", re.DOTALL)

for file in os.listdir(js_dir):
    if not file.endswith('.js'): continue
    file_path = os.path.join(js_dir, file)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if legend_pattern.search(content):
        new_content = legend_pattern.sub('', content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Removed legend from {file}")
