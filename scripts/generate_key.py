#!/usr/bin/env python3
"""Generate encryption key for API keys storage"""

try:
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    print("Generated encryption key:")
    print(key.decode())
    print("\nAdd this to your backend/.env file:")
    print(f"ENCRYPTION_KEY={key.decode()}")
except ImportError:
    print("Error: cryptography module not installed.")
    print("Please install it first: pip install cryptography")
    print("\nOr use this temporary key (NOT for production):")
    print("ENCRYPTION_KEY=your-temporary-key-here")
