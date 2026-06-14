import re

with open('frontend/js/state.js', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('signalData: null,', 'signalData: null,\n    ensembleData: null,')

with open('frontend/js/state.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated state.js")
