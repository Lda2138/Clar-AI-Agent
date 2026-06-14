import os
import re

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Force replace .analysis-tabs-indicator
pattern = r'\.analysis-tabs-indicator\s*\{[^}]*\}'
replacement = '''.analysis-tabs-indicator {
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
  }'''
content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated indicator")
