import os
import re

file_path = 'frontend/js/charts.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The ECharts option object has series: [{ type: 'graph', ... }].
# I'll just add legend: { show: false }, before series:
if 'legend: { show: false },' not in content:
    content = content.replace('series: [{', 'legend: { show: false },\n            series: [{')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added legend: { show: false } to charts.js")
else:
    print("Already hidden.")
