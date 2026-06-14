from bs4 import BeautifulSoup
import sys

with open('scratch/body_content.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

for child in soup.contents:
    if child.name:
        print(f"<{child.name} id='{child.get('id', '')}' class='{child.get('class', '')}'>")
