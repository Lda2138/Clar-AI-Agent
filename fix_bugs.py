# coding: utf-8
import os
import re

found = False
for root, dirs, files in os.walk('c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/frontend'):
    for file in files:
        if file.endswith('.js') or file.endswith('.html'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for legend config
            if "['章节', '小节', '核心知识点']" in content:
                print(f"Found in {file_path}")
                # Remove the legend
                pattern = re.compile(r"legend:\s*\[\s*\{\s*data:\s*\['章节',\s*'小节',\s*'核心知识点'\],\s*textStyle:[^\]]+\]\s*\},?", re.DOTALL)
                pattern2 = re.compile(r"legend:\s*\[\{\s*data:\s*\['章节',\s*'小节',\s*'核心知识点'\][^\}]+\}\],?", re.DOTALL)
                
                # Let's do a simpler string replace since regex might miss some spaces
                
                # We know the approximate block. Let's just find "legend: [{" and "bottom: 10" "}]"
                start = content.find("legend: [{")
                if start != -1 and "['章节', '小节', '核心知识点']" in content[start:start+200]:
                    end = content.find("}],", start)
                    if end != -1:
                        content = content[:start] + content[end+3:]
                        with open(file_path, 'w', encoding='utf-8') as fw:
                            fw.write(content)
                        print(f"Removed legend block from {file_path}")
                        found = True

# Also fix the chat_routes.py Easter Egg logic
backend_path = 'c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu/backend/chat_routes.py'
with open(backend_path, 'r', encoding='utf-8') as f:
    b_content = f.read()

# Current logic might have mojibake or be literal. 
# We look for: if "老师" in prompt_lower and ("最好" in prompt_lower or "推荐" in prompt_lower or "哪个" in prompt_lower):
old_cond = 'if "老师" in prompt_lower and ("最好" in prompt_lower or "推荐" in prompt_lower or "哪个" in prompt_lower):'
new_cond = 'if "老师" in prompt_lower and ("最好" in prompt_lower or "推荐" in prompt_lower or "哪个" in prompt_lower) and "随机" in prompt_lower:'

if old_cond in b_content:
    b_content = b_content.replace(old_cond, new_cond)
    with open(backend_path, 'w', encoding='utf-8') as f:
        f.write(b_content)
    print("Fixed Easter Egg condition.")
else:
    print("Could not find the Easter egg condition to replace.")

