import os
import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

body_match = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
if body_match:
    body_content = body_match.group(1)
    with open('scratch/body_content.html', 'w', encoding='utf-8') as f:
        f.write(body_content)
    print("Extracted body_content.html")
