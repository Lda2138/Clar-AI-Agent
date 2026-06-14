import os

replacements = {
    'background: rgba(201, 92, 22, 0.05); border-left: 3px solid #356099; color: #2a4e7c;': 'background: rgba(53, 96, 153, 0.05); border-left: 3px solid #356099; color: #2a4e7c;',
    'background: rgba(53, 96, 153, 0.05); border-left: 3px solid #C95C16;': 'background: rgba(53, 96, 153, 0.05); border-left: 3px solid #356099;',
    'background: rgba(53,96,153,0.05); border-left: 3px solid #C95C16;': 'background: rgba(53, 96, 153, 0.05); border-left: 3px solid #356099;',
    'background: rgba(66,133,244,0.05); border-left: 3px solid #C95C16;': 'background: rgba(53, 96, 153, 0.05); border-left: 3px solid #356099;'
}

def replace_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    if original != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

js_dir = 'frontend/js'
for f in os.listdir(js_dir):
    if f.endswith('.js'):
        replace_in_file(os.path.join(js_dir, f))
