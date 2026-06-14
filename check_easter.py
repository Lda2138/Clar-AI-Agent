import os

file_path = 'backend/chat_routes.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('# 5. Easter Egg for Teacher Recommendation')
end_idx = content.find('def event_generator():')

if start_idx != -1 and end_idx != -1:
    print(content[start_idx:end_idx])
else:
    print("Not found")
