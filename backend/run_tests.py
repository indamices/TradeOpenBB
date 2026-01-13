#!/usr/bin/env python3
"""Run tests with typing fix"""
import sys
import os

# Fix typing.Self before importing anything
exec(open('fix_typing_self.py').read())

# Add system site-packages to path
import site
site_packages = site.getsitepackages()
for sp in site_packages:
    if sp not in sys.path:
        sys.path.insert(0, sp)

# Fix typing in system modules
import typing
try:
    from typing_extensions import Self
    if not hasattr(typing, 'Self'):
        typing.Self = Self
        sys.modules['typing'].Self = Self
except ImportError:
    pass

# Now run pytest
import subprocess
import pytest

if __name__ == '__main__':
    # Run pytest
    exit_code = pytest.main([
        'tests/',
        '-v',
        '--tb=short',
        '--maxfail=10'
    ])
    sys.exit(exit_code)
