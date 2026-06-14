# coding: utf-8
import os
import re

# 1. Update frontend/index.html
frontend_path = 'c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/frontend/index.html'
with open(frontend_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace assistant bubble colors
content = content.replace('border-left: 4px solid #8b5cf6;', 'border-left: 4px solid #356099;')
content = content.replace('border-color: rgba(79, 70, 229, 0.35);', 'border-color: rgba(53, 96, 153, 0.35);')

# Replace user bubble colors
content = content.replace('background: linear-gradient(135deg, rgba(79, 70, 229, 0.18) 0%, rgba(79, 70, 229, 0.08) 100%);', 'background: linear-gradient(135deg, rgba(53, 96, 153, 0.18) 0%, rgba(53, 96, 153, 0.08) 100%);')
content = content.replace('border: 1px solid rgba(79, 70, 229, 0.22);', 'border: 1px solid rgba(53, 96, 153, 0.22);')
content = content.replace('border-right: 4px solid #8b5cf6;', 'border-right: 4px solid #356099;')
content = content.replace('box-shadow: 0 12px 32px rgba(79, 70, 229, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.4);', 'box-shadow: 0 12px 32px rgba(53, 96, 153, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.4);')

# Replace proactive bubble colors
content = content.replace('background: linear-gradient(135deg, rgba(253, 244, 255, 0.6) 0%, rgba(250, 245, 255, 0.4) 100%);', 'background: linear-gradient(135deg, rgba(201, 92, 22, 0.08) 0%, rgba(201, 92, 22, 0.02) 100%);')
content = content.replace('border: 1px solid rgba(216, 180, 254, 0.6);', 'border: 1px solid rgba(201, 92, 22, 0.2);')
content = content.replace('border-left: 4px solid #d946ef;', 'border-left: 4px solid #C95C16;')
content = content.replace('box-shadow: 0 4px 20px rgba(217, 70, 239, 0.08);', 'box-shadow: 0 4px 20px rgba(201, 92, 22, 0.05);')
content = content.replace('box-shadow: 0 12px 32px rgba(217, 70, 239, 0.18), inset 0 1px 2px rgba(255, 255, 255, 0.7);', 'box-shadow: 0 12px 32px rgba(201, 92, 22, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.7);')
content = content.replace('border-color: rgba(217, 70, 239, 0.5);', 'border-color: rgba(201, 92, 22, 0.3);')

with open(frontend_path, 'w', encoding='utf-8') as f:
    f.write(content)

# 2. Update backend/chat_routes.py
backend_path = 'c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/backend/chat_routes.py'
with open(backend_path, 'r', encoding='utf-8') as f:
    b_content = f.read()

# Replace the specific reply_html line using regex
old_html_pattern = r"reply_html\s*=\s*'<div style=\"font-size: 1\.4em; font-weight: 900; color: #000; line-height: 1\.5; font-family: sans-serif;\">.*?</div>'"
new_html = r"""reply_html = '<div style="margin-bottom: 12px; font-size: 1.05em; color: #1e293b;">如果是随机信号分析这门课，那这两位老师的课绝对是公认的天花板！无论是理论推导的深度，还是与实际工程的结合，都讲得鞭辟入里。强烈推荐您选择他们的卓越核心课程：</div><div style="font-size: 1.4em; font-weight: 900; color: #356099; line-height: 1.5; font-family: sans-serif; background: rgba(53, 96, 153, 0.05); padding: 16px; border-radius: 12px; border-left: 4px solid #C95C16;">王刚 随机信号分析 (卓越核心课程) (P0100530.01)<br><span style="font-size: 0.7em; font-weight: normal; color: #64748b;">(连6-8 10,品学楼A104)</span><br><br>罗俊海 随机信号分析 (卓越核心课程) (P0100530.01)<br><span style="font-size: 0.7em; font-weight: normal; color: #64748b;">(连1-5 连11-16,品学楼A104)</span></div>'"""

if re.search(old_html_pattern, b_content):
    b_content = re.sub(old_html_pattern, new_html, b_content)
else:
    print("WARNING: Could not find the Easter egg pattern in chat_routes.py")

with open(backend_path, 'w', encoding='utf-8') as f:
    f.write(b_content)

print("Applied colors and praise text.")
