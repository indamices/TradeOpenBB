#!/usr/bin/env python3
"""Fix typing.Self at system level"""
import sys
import site
import typing

# Get system site-packages
site_packages = site.getsitepackages()[0]
print(f"System site-packages: {site_packages}")

# Try to add Self to typing module
try:
    from typing_extensions import Self
    if not hasattr(typing, 'Self'):
        typing.Self = Self
        sys.modules['typing'].Self = Self
        print("✅ Added Self to typing module")
    else:
        print("✅ Self already exists in typing module")
except ImportError:
    print("❌ typing_extensions not available")
    # Try to install it first
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'typing-extensions'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        from typing_extensions import Self
        typing.Self = Self
        sys.modules['typing'].Self = Self
        print("✅ Installed typing-extensions and added Self")
    else:
        print("❌ Failed to install typing-extensions")
