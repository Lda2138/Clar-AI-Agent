import re

with open('frontend/js/ui.js', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('S.signalData = data; S.filteredData = null;', 'S.signalData = data; S.filteredData = null; S.ensembleData = null;')

with open('frontend/js/ui.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Cleared ensembleData in generateSignal")
