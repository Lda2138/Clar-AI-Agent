import os

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('legend:')
while idx != -1:
    print(content[idx:idx+200])
    idx = content.find('legend:', idx+1)
