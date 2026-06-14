import os
import re

found = False
for root, dirs, files in os.walk('frontend'):
    for file in files:
        if file.endswith('.js') or file.endswith('.html'):
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                content = f.read()
                if "['章节', '小节', '核心知识点']" in content or "legend:" in content:
                    idx = content.find("['章节', '小节', '核心知识点']")
                    if idx != -1:
                        print(f"Found EXACT STRING in {file}")
                        print(content[idx-100:idx+200])
                        found = True
if not found:
    print("Not found.")
