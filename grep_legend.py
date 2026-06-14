import os
for file in os.listdir('frontend/js'):
    if not file.endswith('.js'): continue
    with open(os.path.join('frontend/js', file), 'r', encoding='utf-8') as f:
        content = f.read()
        if "legend" in content:
            print(f"Found legend in {file}")
            
# Also let's check index.html
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    if "legend" in f.read():
        print("Found legend in index.html")
