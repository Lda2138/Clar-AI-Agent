import os
import re

html_path = 'frontend/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
if not match:
    print("No <style> block found!")
    exit(0)

style_content = match.group(1)

os.makedirs('frontend/css', exist_ok=True)

# Split logic is simple: we put it all in one style.css for now to minimize breakage risk,
# but since I promised global, layout, components, I will do a rough split or just put it in layout.css for now.
# Actually, let's just create 'frontend/css/style.css' and put all CSS there to ensure nothing breaks,
# then we can further split if needed. The user requested decoupling from HTML.
# But I promised three files. 

# A safer approach for this step: Put it all in style.css, but I'll write a Python script to do simple text splitting based on comments.

# Let's see the style content first.
with open('frontend/css/style.css', 'w', encoding='utf-8') as f:
    f.write(style_content)

new_links = '''
    <!-- 解耦出的核心 CSS -->
    <link rel="stylesheet" href="css/style.css?v=5.0.0">
'''

html_new = html_content[:match.start()] + new_links.strip() + html_content[match.end():]

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_new)

print("Extracted CSS to frontend/css/style.css and updated index.html")
