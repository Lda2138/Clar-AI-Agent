import re

with open('scratch/body_content.html', 'r', encoding='utf-8') as f:
    html = f.read()

# find top level tags
tags = re.findall(r'<(div|header|footer|aside|main|script|svg)[^>]*>', html)
print(tags)

tags_with_attrs = re.findall(r'<([a-z]+)\s+([^>]*id="[^"]*"[^>]*|[^>]*class="[^"]*"[^>]*)>', html)
for t, attrs in tags_with_attrs:
    if "main-content" in attrs or "ai-panel" in attrs or "bottom-bar" in attrs or "header" in attrs or "cards-wrapper" in attrs:
        print(f"<{t} {attrs}>")

