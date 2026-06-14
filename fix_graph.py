with open('frontend/js/charts.js', 'r', encoding='utf-8') as f:
    content = f.read()

import re
# Remove the category assignment line in the nodeObj
content = re.sub(r'category:\s*n\.category[^,]+,', '', content)

with open('frontend/js/charts.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed category mapping from nodes.")
