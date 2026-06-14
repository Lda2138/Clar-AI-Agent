import os
for root, dirs, files in os.walk('frontend'):
    for file in files:
        if file.endswith('.html') or file.endswith('.js'):
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                content = f.read()
                if "уб╫з" in content:
                    print(f"Found 'уб╫з' in {file}")
