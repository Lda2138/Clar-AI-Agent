with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('v=2.1.3', 'v=2.1.4')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Cache busted: v=2.1.3 -> v=2.1.4")
