"""
Fix imports before starting the application
This should be imported before any other modules
"""
import sys
import os

# Add typing fixes
try:
    from .fix_typing_notrequired import *
except ImportError:
    try:
        import fix_typing_notrequired
    except ImportError:
        pass

# Try to fix pydantic-core DLL issue by preloading
try:
    # Try to import and reload pydantic_core
    import importlib
    if 'pydantic_core' in sys.modules:
        importlib.reload(sys.modules['pydantic_core'])
except Exception as e:
    print(f"Warning: Could not preload pydantic_core: {e}")
