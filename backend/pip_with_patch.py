#!/usr/bin/env python3
"""Run pip with typing.Self patch"""
import sys
import site

# Add typing.Self before importing pip
site.addsitedir(site.getsitepackages()[0])
try:
    import _typing_patch
    import typing
    if not hasattr(typing, 'Self'):
        from typing_extensions import Self
        typing.Self = Self
        sys.modules['typing'].Self = Self
except:
    pass

# Now run pip
import pip._internal.main
sys.exit(pip._internal.main.main())
