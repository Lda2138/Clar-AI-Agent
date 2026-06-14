# coding: utf-8
import os
import re

with open('c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

matches = re.finditer(r'.{0,50}章节.{0,50}', html)
found = False
for m in matches:
    print("Match:", m.group(0))
    found = True
if not found:
    print("No matches for 章节 in index.html")
    
# Let's also check backend/knowledge_routes.py
with open('c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/backend/knowledge_routes.py', 'r', encoding='utf-8') as f:
    backend_content = f.read()

matches = re.finditer(r'.{0,50}legend.{0,50}', backend_content)
for m in matches:
    print("Backend match legend:", m.group(0))
    
matches = re.finditer(r'.{0,50}图例.{0,50}', backend_content)
for m in matches:
    print("Backend match 图例:", m.group(0))
