import os
import re

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Button Hover
content = content.replace('linear-gradient(135deg, #b062fc, #6e72f9)', 'linear-gradient(135deg, #5A85C3, #2a4e7c)')

# Fix Analysis Tab Button Gradient -> Solid Blue
content = content.replace('.analysis-tab-btn.active {\n      color: #ffffff;\n  }', '.analysis-tab-btn.active {\n      color: #ffffff;\n      background: #356099;\n  }')

# Ensure no hidden orange gradients in index.html for .analysis-tab-btn.active 
# Actually, the python script earlier might have made it background: linear-gradient(135deg, #4c85cc, #356099)
# Wait, let me just replace all linear-gradient(135deg, #4c85cc, #356099) with #356099 for analysis-tab-btn if it exists.
content = re.sub(
    r'\.analysis-tab-btn\.active \{[\s\S]*?\}',
    '.analysis-tab-btn.active {\n      color: #ffffff;\n      background: #356099;\n      border-color: transparent;\n  }',
    content
)

# Fix Clar Logo Styling
content = content.replace('<span>Clar <small', '<span><span style="color: var(--brand-orange)">C</span>lar <small')

# Fix Main Menu Border Radii
# Outer bottom bar is already 24px
content = re.sub(
    r'\.nav-tabs \{ display: flex; gap: 4px; position: relative; z-index: 1; background: rgba\(15, 23, 42, 0\.05\); border-radius: 24px; padding: 4px; border: 1px solid rgba\(15, 23, 42, 0\.05\); \}',
    '.nav-tabs { display: flex; gap: 4px; position: relative; z-index: 1; background: rgba(15, 23, 42, 0.05); border-radius: 16px; padding: 4px; border: 1px solid rgba(15, 23, 42, 0.05); }',
    content
)

content = re.sub(
    r'\.nav-indicator \{[\s\S]*?opacity: 0; /\* Hidden until initialized by JS \*/\n  \}',
    '''.nav-indicator {
      position: absolute;
      top: 0; left: 0;
      height: 100%;
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

content = re.sub(
    r'\.tab-item \{[\s\S]*?transition: all 0\.3s cubic-bezier\(0\.25, 0\.8, 0\.25, 1\);\n      z-index: 2;\n  \}',
    '''.tab-item {
      padding: 8px 24px; border: 1px solid transparent; background: transparent; cursor: pointer;
      font-size: 13px; color: #64748b; border-radius: 12px; font-weight: 600;
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
      z-index: 2;
  }''',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Backend Knowledge Nodes
backend_path = 'backend/knowledge_routes.py'
with open(backend_path, 'r', encoding='utf-8') as f:
    backend_content = f.read()

# Replace google palette with Brand Blue / Orange palette
backend_content = backend_content.replace('#4285f4', '#4c85cc') # Base blue -> light brand blue
backend_content = backend_content.replace('#34a853', '#356099') # Section green -> Primary brand blue
backend_content = backend_content.replace('#ea4335', '#C95C16') # Important red -> Brand Orange
backend_content = backend_content.replace('#fbbc04', '#E47732') # Topic yellow -> Light brand orange

with open(backend_path, 'w', encoding='utf-8') as f:
    f.write(backend_content)

print("Updates applied")
