"""
Fix typing.NotRequired for Python 3.11.0a1
"""
import sys
import typing

# Check if NotRequired exists
if not hasattr(typing, 'NotRequired'):
    # Add NotRequired from typing_extensions if available
    try:
        from typing_extensions import NotRequired
        typing.NotRequired = NotRequired
        print("✅ Added NotRequired from typing_extensions")
    except ImportError:
        # Create a simple placeholder
        from typing import _GenericAlias
        class _NotRequiredMeta(type):
            def __getitem__(self, item):
                return item
        NotRequired = _NotRequiredMeta('NotRequired', (), {})
        typing.NotRequired = NotRequired
        print("✅ Created NotRequired placeholder")

# Also check for Required
if not hasattr(typing, 'Required'):
    try:
        from typing_extensions import Required
        typing.Required = Required
    except ImportError:
        class _RequiredMeta(type):
            def __getitem__(self, item):
                return item
        Required = _RequiredMeta('Required', (), {})
        typing.Required = Required
