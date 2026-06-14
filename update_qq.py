# coding: utf-8
import os

backend_path = 'c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/backend/chat_routes.py'
with open(backend_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_str = '"quick_questions": [],'
new_str = '"quick_questions": ["王刚老师的授课风格是怎样的？", "罗俊海老师的考试难吗？", "怎么才能选上卓越核心课程？"],'

if old_str in content:
    start_idx = content.find('def easter_egg_generator():')
    end_idx = content.find('return StreamingResponse(easter_egg_generator()', start_idx)
    if start_idx != -1 and end_idx != -1:
        block = content[start_idx:end_idx]
        new_block = block.replace(old_str, new_str)
        content = content[:start_idx] + new_block + content[end_idx:]
        with open(backend_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated quick questions for Easter egg.")
    else:
        print("Block not found.")
else:
    print("old_str not found.")
