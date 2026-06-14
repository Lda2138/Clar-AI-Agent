import os
import re

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Custom Webkit Scrollbars (Global)
# Replace existing if there, otherwise add to the end of CSS
scrollbar_css = '''
  /* Premium Glassmorphic Global Scrollbars */
  ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
  }
  ::-webkit-scrollbar-track {
      background: transparent;
  }
  ::-webkit-scrollbar-thumb {
      background: rgba(53, 96, 153, 0.2);
      border-radius: 6px;
      transition: background 0.3s;
  }
  ::-webkit-scrollbar-thumb:hover {
      background: rgba(53, 96, 153, 0.4);
  }
  ::-webkit-scrollbar-corner {
      background: transparent;
  }
  '''
if '/* Premium Glassmorphic Floating Scrollbars */' in content:
    content = re.sub(r'/\* Premium Glassmorphic Floating Scrollbars \*/[\s\S]*?::-webkit-scrollbar-thumb:active \{[^\}]*\}', scrollbar_css, content)
else:
    content = content.replace('</style>', scrollbar_css + '\n</style>')

# 2. Input/Select Focus States & Transitions
content = re.sub(
    r'\.ctrl-item input, \.ctrl-item select \{[\s\S]*?\}',
    '''.ctrl-item input, .ctrl-item select {
      border: 1px solid transparent; background: rgba(255, 255, 255, 0.3); outline: none; font-size: 13px; color: #1e293b; width: 75px; font-weight: 500;
      padding: 4px 6px; border-radius: 6px; transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  }
  .ctrl-item input:focus, .ctrl-item select:focus {
      background: #ffffff;
      border-color: #4c85cc;
      box-shadow: 0 0 0 3px rgba(53, 96, 153, 0.15);
  }''',
    content
)

# 3. Micro-animations for buttons
content = re.sub(
    r'\.btn-apply:active \{[^\}]*\}',
    '''.btn-apply:active { transform: translateY(0) scale(0.96); box-shadow: 0 2px 8px rgba(53, 96, 153, 0.2); }''',
    content
)
if '.btn-apply:active {' not in content:
    # Add active state if it doesn't exist
    content = content.replace('.btn-apply:hover {', '.btn-apply:active { transform: translateY(0) scale(0.96); box-shadow: 0 2px 8px rgba(53, 96, 153, 0.2); }\n  .btn-apply:hover {')

# 4. Control Panel Labels Typography
content = re.sub(
    r'\.ctrl-item label \{[^\}]*\}',
    '''.ctrl-item label { color: #64748b; font-size: 12px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap; }''',
    content
)

# 5. Chat Box Typography and Markdown elements
content = re.sub(
    r'\.bubble \{[\s\S]*?\}',
    '''.bubble {
      padding: 14px 18px; border-radius: 16px; font-size: 14.5px; line-height: 1.65; max-width: 85%;
      box-shadow: 0 4px 15px rgba(0,0,0,0.03); letter-spacing: 0.2px; word-wrap: break-word;
  }
  .bubble code {
      background: rgba(0, 0, 0, 0.05); padding: 2px 6px; border-radius: 6px; font-size: 0.9em; font-family: 'Consolas', monospace;
  }
  .bubble pre {
      background: rgba(15, 23, 42, 0.04); padding: 12px; border-radius: 12px; overflow-x: auto; font-size: 0.9em; font-family: 'Consolas', monospace; border: 1px solid rgba(15, 23, 42, 0.05);
  }
  .bubble table {
      width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.95em;
  }
  .bubble th, .bubble td {
      border: 1px solid rgba(15, 23, 42, 0.1); padding: 8px 12px; text-align: left;
  }
  .bubble th {
      background: rgba(15, 23, 42, 0.03); font-weight: 600; color: #334155;
  }
  ''',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Aesthetic updates successfully injected via python.")
