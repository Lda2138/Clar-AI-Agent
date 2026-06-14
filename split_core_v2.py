import os

with open('core/signal_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

header = '''import numpy as np
from scipy import signal as scipy_signal
from typing import Dict, Tuple, Optional, Any
'''

lines = content.split('\n')

parts = {'header': [], 'generators': [], 'analyzers': [], 'filters': [], 'other': []}
current_part = 'header'

for line in lines:
    if '# ── 信号生成' in line:
        current_part = 'generators'
    elif '# ── 特征分析' in line:
        current_part = 'analyzers'
    elif '# ── 信号滤波' in line:
        current_part = 'filters'
    
    parts[current_part].append(line)

os.makedirs('core/signal', exist_ok=True)

with open('core/signal/generators.py', 'w', encoding='utf-8') as f:
    f.write(header + '\n' + '\n'.join(parts['generators']))

with open('core/signal/analyzers.py', 'w', encoding='utf-8') as f:
    f.write(header + '\n' + '\n'.join(parts['analyzers']))

with open('core/signal/filters.py', 'w', encoding='utf-8') as f:
    f.write(header + '\n' + '\n'.join(parts['filters']))

facade = '''"""
Facade for signal operations. 
System decoupled into:
- core.signal.generators
- core.signal.analyzers
- core.signal.filters
"""
from .signal.generators import *
from .signal.analyzers import *
from .signal.filters import *

try:
    from .signal.generators import _SIGNAL_GENERATORS
except ImportError:
    pass
'''

with open('core/signal_engine.py', 'w', encoding='utf-8') as f:
    f.write(facade)

print("Decoupling complete")
