import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Bump versions
html = html.replace('v=2.2.0', 'v=3.0.0')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Cache busted in index.html.")
