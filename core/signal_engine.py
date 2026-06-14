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

try:
    from .signal.generators import _SIGNAL_GENERATORS
except ImportError:
    pass
