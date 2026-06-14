import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

footer_match = re.search(r'(<footer id="bottom-bar">.*?</footer>)', html, re.DOTALL)
if footer_match:
    with open('scratch/footer.html', 'w', encoding='utf-8') as f:
        f.write(footer_match.group(1))
    print("Found footer")
