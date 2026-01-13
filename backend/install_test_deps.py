#!/usr/bin/env python3
"""Install test dependencies with typing fix"""
import sys
import subprocess

# Fix typing.Self before importing anything
exec(open('fix_typing_self.py').read())

# Install dependencies
packages = ['pytest', 'pytest-asyncio', 'pytest-cov', 'httpx']
for package in packages:
    print(f"Installing {package}...")
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', package], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {package} installed")
    else:
        print(f"❌ {package} failed: {result.stderr[-200:]}")

print("\n✅ Installation complete!")
