import os

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add font-family inherit to form elements
content = content.replace(
    'body {\n    font-family: \'Times New Roman\', SimSun, \'宋体\', serif;\n    font-size: 14.5px;',
    'body {\n    font-family: \'Times New Roman\', SimSun, \'宋体\', serif;\n    font-size: 14.5px;\n}\nbutton, input, textarea, select {\n    font-family: inherit;\n}\nbody {\n    font-size: 14.5px;'
)

# 2. Clean button gradients
content = content.replace(
    'background: linear-gradient(135deg, #10b981, #059669);\n    color: #fff; border: 1px solid rgba(255, 255, 255, 0.25);',
    'background: #fff;\n    color: #1e293b; border: 1px solid #cbd5e1;'
)
content = content.replace(
    'background: linear-gradient(135deg, #34d399, #047857);',
    'background: #f8fafc;'
)
content = content.replace(
    'background: linear-gradient(135deg, #8b5cf6, #6d28d9);\n    color: #fff; border: 1px solid rgba(255, 255, 255, 0.25);',
    'background: #fff;\n    color: #1e293b; border: 1px solid #cbd5e1;'
)
content = content.replace(
    'background: linear-gradient(135deg, #a78bfa, #5b21b6);',
    'background: #f8fafc;'
)
# For btn-apply gradient
content = content.replace(
    'background: linear-gradient(135deg, #356099, #284c7c);\n    color: #fff; border: 1px solid rgba(255, 255, 255, 0.25);',
    'background: #fff;\n    color: #1e293b; border: 1px solid #cbd5e1;'
)
content = content.replace(
    'background: linear-gradient(135deg, #4f80c6, #1c3b63);',
    'background: #f8fafc;'
)

# 3. Restore clar ball and move its classic state
content = content.replace(
    'top: 36px;\n    right: 44px;',
    'top: 36px;\n    right: 120px;'
)

clar_ball_markup = '''<div id="ai-mode-sprite-toggle" class="ai-mode-sprite-toggle state-classic" title="双击切换 AI 模式 (Classic / Clar-ball)">
    <div class="sprite-core"></div>
</div>'''

content = content.replace(
    '<!-- Removed AI Mode Sprite to clean up layout -->',
    clar_ball_markup
)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updates applied.")
