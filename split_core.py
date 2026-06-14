import os

with open('core/signal_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# For a quick and safe decoupling that guarantees we don't break existing Python logic:
# 1. Write the exact same content to generators, analyzers, filters.
# 2. Modify core/signal_engine.py to import everything from them.
# 3. Later we can prune unused functions in each file. For now, the files are separate domains.
# Actually, the user wants true decoupling so they can be modified independently. Let's do a simple regex split.

parts = content.split('# ── ')

generators_part = ""
analyzers_part = ""
filters_part = ""
header = ""

for p in parts:
    if p.startswith('import ') or 'import ' in p and not p.startswith('信号生成'):
        header = p
    if p.startswith('信号生成'):
        generators_part = '# ── ' + p
    elif p.startswith('特征分析'):
        analyzers_part = '# ── ' + p
    elif p.startswith('信号滤波'):
        filters_part = '# ── ' + p

# Reconstruct
def build_file(header, body):
    # Ensure imports exist
    imp = "import numpy as np\nfrom scipy import signal as scipy_signal\nfrom typing import Dict, Tuple, Optional, Any\n"
    return imp + "\n" + body

with open('core/signal/generators.py', 'w', encoding='utf-8') as f:
    f.write(build_file(header, generators_part))

with open('core/signal/analyzers.py', 'w', encoding='utf-8') as f:
    f.write(build_file(header, analyzers_part))

with open('core/signal/filters.py', 'w', encoding='utf-8') as f:
    f.write(build_file(header, filters_part))

# Now rewrite signal_engine.py to be a facade
facade = '''# core/signal_engine.py
"""
Facade for signal operations. 
System decoupled into:
- core.signal.generators
- core.signal.analyzers
- core.signal.filters
"""

from .signal.generators import *
from .signal.analyzers import *
from .signal.filters import *

# Export the generator map if it exists
try:
    from .signal.generators import _SIGNAL_GENERATORS
except ImportError:
    pass
'''

with open('core/signal_engine.py', 'w', encoding='utf-8') as f:
    f.write(facade)

print("Decoupled signal_engine.py into core/signal/*")
