import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace bottom-bar with main-nav-tabs
js = js.replace(
    "document.getElementById('bottom-bar').addEventListener",
    "document.getElementById('main-nav-tabs').addEventListener"
)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("app.js fixed.")
