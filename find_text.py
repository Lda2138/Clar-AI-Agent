with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()
    
# Let's search for "уб╫з" regardless of where it is
import re
matches = re.finditer(r'.{0,50}уб╫з.{0,50}', html)
for m in matches:
    print(m.group(0))
