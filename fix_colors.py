import os

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Metric values to Blue instead of Orange
content = content.replace('.metric .val { font-size: 18px; font-weight: 700; color: #C95C16; }', 
                          '.metric .val { font-size: 18px; font-weight: 700; color: #356099; }')

# 2. KC cards - Primary is Blue, Secondary is Orange
content = content.replace('.kc-card--primary::before { content: \'\'; position: absolute; left: 0; top: 15%; height: 70%; width: 4px; background: #C95C16;',
                          '.kc-card--primary::before { content: \'\'; position: absolute; left: 0; top: 15%; height: 70%; width: 4px; background: #356099;')

# 3. Typing dots to Blue
content = content.replace('.typing-dots span { width: 6px; height: 6px; background: #C95C16;',
                          '.typing-dots span { width: 6px; height: 6px; background: #356099;')

# 4. Chat messages / blockquotes
content = content.replace('color: #C95C16; border-color: rgba(201, 92, 22, 0.3);',
                          'color: #2a4e7c; border-color: rgba(53, 96, 153, 0.3);')
content = content.replace('border-left: 4px solid #C95C16;', 'border-left: 4px solid #356099;')
content = content.replace('border-right: 4px solid #C95C16;', 'border-right: 4px solid #356099;')
content = content.replace('background: rgba(201, 92, 22, 0.08); padding: 2px 6px; border-radius: 4px; color: #C95C16; font-weight: 600;',
                          'background: rgba(15, 23, 42, 0.05); padding: 2px 6px; border-radius: 4px; color: #0f172a; font-weight: 600;')
content = content.replace('border-left: 3px solid #C95C16; padding: 8px 14px; margin: 8px 0;',
                          'border-left: 3px solid #356099; padding: 8px 14px; margin: 8px 0;')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
