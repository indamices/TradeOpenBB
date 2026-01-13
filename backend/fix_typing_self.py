"""Fix typing.Self for Python 3.11.0 compatibility"""
import sys
import typing

# Add Self type for Python 3.11.0
if not hasattr(typing, 'Self'):
    from typing_extensions import Self as _Self
    typing.Self = _Self
    sys.modules['typing'].Self = _Self
    print("Added Self to typing module")
