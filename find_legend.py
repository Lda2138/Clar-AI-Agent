import os

js_dir = 'frontend/js'
for file in os.listdir(js_dir):
    if not file.endswith('.js'): continue
    file_path = os.path.join(js_dir, file)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    idx = content.find('legend: [{')
    if idx != -1:
        print(f"Found in {file}:")
        print(content[idx:idx+200])
