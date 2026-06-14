import re
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()
html = re.sub(r'v=\d+\.\d+\.\d+', 'v=6.0.0', html)
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
