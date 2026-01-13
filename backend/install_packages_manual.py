#!/usr/bin/env python3
"""Manually install packages by downloading wheels"""

import urllib.request
import zipfile
import os
import site
import json

# Package URLs (wheel files from PyPI)
PACKAGES = {
    'fastapi': 'https://files.pythonhosted.org/packages/py3/f/fastapi/fastapi-0.115.0-py3-none-any.whl',
    'uvicorn': 'https://files.pythonhosted.org/packages/py3/u/uvicorn/uvicorn-0.32.1-py3-none-any.whl',
    'sqlalchemy': 'https://files.pythonhosted.org/packages/py3/s/sqlalchemy/SQLAlchemy-2.0.36-py3-none-any.whl',
    'psycopg2_binary': 'https://files.pythonhosted.org/packages/py3/p/psycopg2-binary/psycopg2_binary-2.9.10-cp311-cp311-win_amd64.whl',
    'pydantic': 'https://files.pythonhosted.org/packages/py3/p/pydantic/pydantic-2.10.4-py3-none-any.whl',
    'pandas': 'https://files.pythonhosted.org/packages/py3/p/pandas/pandas-2.2.3-cp311-cp311-win_amd64.whl',
    'numpy': 'https://files.pythonhosted.org/packages/py3/n/numpy/numpy-2.2.1-cp311-cp311-win_amd64.whl',
    'yfinance': 'https://files.pythonhosted.org/packages/py3/y/yfinance/yfinance-0.2.49-py3-none-any.whl',
    'requests': 'https://files.pythonhosted.org/packages/py3/r/requests/requests-2.32.3-py3-none-any.whl',
    'python_dotenv': 'https://files.pythonhosted.org/packages/py3/p/python-dotenv/python_dotenv-1.0.1-py3-none-any.whl',
    'cryptography': 'https://files.pythonhosted.org/packages/py3/c/cryptography/cryptography-43.0.3-cp311-cp311-win_amd64.whl',
    'cachetools': 'https://files.pythonhosted.org/packages/py3/c/cachetools/cachetools-5.4.0-py3-none-any.whl',
}

def install_package(name, url, target_dir):
    """Download and install a package wheel"""
    print(f"Installing {name}...")
    try:
        wheel_file = f"{name}.whl"
        urllib.request.urlretrieve(url, wheel_file)
        
        with zipfile.ZipFile(wheel_file, 'r') as z:
            z.extractall(target_dir)
        
        os.remove(wheel_file)
        print(f"  ✓ {name} installed")
        return True
    except Exception as e:
        print(f"  ✗ Failed to install {name}: {e}")
        return False

def main():
    # Get site-packages directory
    if hasattr(site, 'getsitepackages'):
        target_dir = site.getsitepackages()[0]
    else:
        import sys
        target_dir = os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages')
    
    print(f"Installing packages to: {target_dir}")
    print()
    
    success = 0
    failed = 0
    
    for name, url in PACKAGES.items():
        if install_package(name, url, target_dir):
            success += 1
        else:
            failed += 1
    
    print()
    print(f"Installation complete: {success} succeeded, {failed} failed")

if __name__ == '__main__':
    main()
