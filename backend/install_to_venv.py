#!/usr/bin/env python3
"""Install packages to virtual environment using direct wheel download"""

import urllib.request
import zipfile
import json
import os
import sys

# Use PyPI JSON API to get latest wheel URLs
def get_package_url(package_name):
    """Get latest wheel URL from PyPI"""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            versions = data['releases']
            latest = max(versions.keys(), key=lambda v: tuple(map(int, v.split('.'))))
            
            # Find a wheel file
            for file_info in versions[latest]:
                if file_info['packagetype'] == 'bdist_wheel':
                    # Prefer Windows wheel if available
                    if 'win_amd64' in file_info['filename'] or 'py3' in file_info['filename']:
                        return file_info['url']
            # Fallback to any wheel
            for file_info in versions[latest]:
                if file_info['packagetype'] == 'bdist_wheel':
                    return file_info['url']
    except Exception as e:
        print(f"Error getting URL for {package_name}: {e}")
    return None

def install_package(package_name, target_dir):
    """Download and install a package"""
    print(f"Installing {package_name}...")
    try:
        url = get_package_url(package_name)
        if not url:
            print(f"  ✗ Could not find wheel for {package_name}")
            return False
        
        wheel_file = f"{package_name}_temp.whl"
        print(f"  Downloading from {url}...")
        urllib.request.urlretrieve(url, wheel_file)
        
        with zipfile.ZipFile(wheel_file, 'r') as z:
            z.extractall(target_dir)
        
        os.remove(wheel_file)
        print(f"  ✓ {package_name} installed")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def main():
    # Get virtual environment site-packages
    venv_lib = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
    if not os.path.exists(venv_lib):
        print("Virtual environment not found. Creating...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
        venv_lib = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
    
    print(f"Installing to: {venv_lib}")
    print()
    
    packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2-binary',
        'pydantic', 'pandas', 'numpy', 'yfinance', 'requests',
        'python-dotenv', 'cryptography', 'cachetools'
    ]
    
    success = 0
    for pkg in packages:
        if install_package(pkg, venv_lib):
            success += 1
        print()
    
    print(f"Installed {success}/{len(packages)} packages")

if __name__ == '__main__':
    main()
