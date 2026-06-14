import os
import re

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update .nav-indicator CSS
content = re.sub(
    r'\.nav-indicator \{[\s\S]*?opacity: 0; /\* Hidden until initialized by JS \*/\n  \}',
    '''.nav-indicator {
      position: absolute;
      top: 4px; left: 0;
      height: calc(100% - 8px);
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
      transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: -1;
      pointer-events: none;
      opacity: 0; /* Hidden until initialized by JS */
  }''',
    content
)

# 2. Update .analysis-tabs-indicator CSS
content = re.sub(
    r'\.analysis-tabs-indicator \{[\s\S]*?z-index: 1;\n      transition: left 0\.3s[\s\S]*?\}',
    '''.analysis-tabs-indicator {
      position: absolute;
      top: 3px;
      bottom: 3px;
      left: 3px;
      width: 0;
      background: #356099;
      border-radius: 9px;
      box-shadow: 0 4px 12px rgba(53, 96, 153, 0.25);
      z-index: 1;
      transition: left 0.3s cubic-bezier(0.25, 1, 0.5, 1), width 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  }''',
    content
)

# 3. Fix Clar Logo Color
content = content.replace('var(--brand-orange)', '#C95C16')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# 4. Fix charts.js legend colors
charts_path = 'frontend/js/charts.js'
with open(charts_path, 'r', encoding='utf-8') as f:
    charts_content = f.read()

# ECharts uses 'color' property in the root options to set the color palette for legends/categories.
if "color: ['#356099', '#4c85cc', '#C95C16']" not in charts_content:
    charts_content = charts_content.replace("legend: [{", "color: ['#356099', '#4c85cc', '#C95C16', '#E47732'],\n              legend: [{")

with open(charts_path, 'w', encoding='utf-8') as f:
    f.write(charts_content)

print("Applied quick fixes")
