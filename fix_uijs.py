import re

with open('frontend/js/ui.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Fix updateNavIndicator
js = re.sub(
    r'indicator\.style\.transform = 	ranslateX\(\$\{activeTab\.offsetLeft\}px\)',
    r'indicator.style.transform = 	ranslateY(px)',
    js
)
js = re.sub(
    r'indicator\.style\.width = \$\{activeTab\.offsetWidth\}px',
    r'indicator.style.height = ${activeTab.offsetHeight}px',
    js
)

# Fix querySelectorAll for tab items
js = js.replace(
    "document.querySelectorAll('#bottom-bar .tab-item')",
    "document.querySelectorAll('.nav-tabs .tab-item')"
)

with open('frontend/js/ui.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("ui.js fixed.")
