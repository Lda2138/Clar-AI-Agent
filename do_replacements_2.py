import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replacements = [
    ('💡 <strong>系统提示：</strong>', '<strong>系统提示：</strong>'),
    ('💡 主动建议', '主动建议'),
    ('📝 系统感知同步：', '系统感知同步：')
]

replace_in_file('frontend/js/chat.js', replacements)
replace_in_file('frontend/js/ui.js', replacements)
replace_in_file('frontend/index.html', replacements)

print("Replacements done.")
