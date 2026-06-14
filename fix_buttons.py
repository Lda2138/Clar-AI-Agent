import os
import re

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Nav tabs and indicator
content = re.sub(
    r'\.nav-tabs \{ display: flex; gap: 8px; position: relative; z-index: 1; \}',
    '.nav-tabs { display: flex; gap: 4px; position: relative; z-index: 1; background: rgba(15, 23, 42, 0.05); border-radius: 24px; padding: 4px; border: 1px solid rgba(15, 23, 42, 0.05); }',
    content
)

content = re.sub(
    r'\.nav-indicator \{[\s\S]*?opacity: 0; /\* Hidden until initialized by JS \*/\n  \}',
    '''.nav-indicator {
      position: absolute;
      top: 0; left: 0;
      height: 100%;
      background: #ffffff;
      border-radius: 20px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
      transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: -1;
      pointer-events: none;
      opacity: 0; /* Hidden until initialized by JS */
  }''',
    content
)

content = re.sub(
    r'\.tab-item \{[\s\S]*?transition: all 0\.3s cubic-bezier\(0\.25, 0\.8, 0\.25, 1\);\n  \}',
    '''.tab-item {
      padding: 8px 24px; border: 1px solid transparent; background: transparent; cursor: pointer;
      font-size: 13px; color: #64748b; border-radius: 20px; font-weight: 600;
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
      z-index: 2;
  }
  .tab-item.active {
      color: #356099;
  }''',
    content
)

# 2. btn-apply colors
content = re.sub(
    r'\.btn-apply \{[\s\S]*?transition: all 0\.3s cubic-bezier\(0\.25, 0\.8, 0\.25, 1\);\n  \}',
    '''.btn-apply {
      display: inline-flex; align-items: center; justify-content: center; line-height: 1;
      padding: 10px 20px; border-radius: 12px; font-size: 13px; font-weight: 600; cursor: pointer;
      background: linear-gradient(135deg, #4c85cc, #356099);
      color: #fff; border: 1px solid rgba(255, 255, 255, 0.25);
      backdrop-filter: blur(10px);
      box-shadow: 0 4px 14px rgba(53, 96, 153, 0.25), inset 0 1px 1px rgba(255, 255, 255, 0.3);
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  }''',
    content
)

content = re.sub(
    r'\.btn-apply:hover \{[\s\S]*?transform: translateY\(-2px\) scale\(1\.02\);\n  \}',
    '''.btn-apply:hover {
      background: linear-gradient(135deg, #5A85C3, #2a4e7c);
      box-shadow: 0 8px 24px rgba(53, 96, 153, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.55);
      transform: translateY(-2px) scale(1.02);
  }''',
    content
)

# 3. Replace all remaining orange-to-blue gradients with pure blue gradients
content = content.replace('#e67322, #356099', '#4c85cc, #356099')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Update JS files for the same gradient
js_dir = 'frontend/js'
for f_name in os.listdir(js_dir):
    if f_name.endswith('.js'):
        f_path = os.path.join(js_dir, f_name)
        with open(f_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        if '#e67322, #356099' in js_content or '#b062fc, #6e72f9' in js_content:
            js_content = js_content.replace('#e67322, #356099', '#4c85cc, #356099')
            js_content = js_content.replace('#b062fc, #6e72f9', '#5A85C3, #2a4e7c')
            with open(f_path, 'w', encoding='utf-8') as f:
                f.write(js_content)
            print('Updated ' + f_name)

print('Done fixing buttons')
