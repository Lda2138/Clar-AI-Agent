with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if '核心知识点' in line:
            print(f'Line {i+1}: {line.strip()}')
