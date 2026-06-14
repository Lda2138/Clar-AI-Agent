with open('frontend/js/charts.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the categories array with an empty array
import re
content = re.sub(r'categories:\s*\[[\s\S]*?\]\s*,', '', content)

with open('frontend/js/charts.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Categories removed from charts.js")
