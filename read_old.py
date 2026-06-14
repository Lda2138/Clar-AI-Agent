import os

file_path = '../agent-by-DZLiu_v2.1.2/frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('.chat-msg {')
end_idx = content.find('.proactive-badge {')

if start_idx != -1 and end_idx != -1:
    print(content[start_idx:end_idx])
else:
    print("Not found")
