#!/usr/bin/env python3
"""Setup encryption key and start backend server"""
import os
import sys
from pathlib import Path

# Generate encryption key
try:
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    print(f"Generated encryption key: {key[:20]}...")
    
    # Update .env file
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        content = env_file.read_text()
        if 'ENCRYPTION_KEY=' in content:
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('ENCRYPTION_KEY='):
                    new_lines.append(f'ENCRYPTION_KEY={key}')
                else:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        else:
            content += f'\nENCRYPTION_KEY={key}'
        env_file.write_text(content)
        print("Encryption key added to .env")
    else:
        print("Warning: .env file not found")
    
except ImportError:
    print("Warning: cryptography not installed, using temporary key")
    key = "temporary-key-not-for-production"
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        content = env_file.read_text()
        if 'ENCRYPTION_KEY=' not in content:
            content += f'\nENCRYPTION_KEY={key}'
            env_file.write_text(content)

# Start server
print("\nStarting FastAPI server...")
os.chdir(Path(__file__).parent)
os.execv(sys.executable, [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'])
