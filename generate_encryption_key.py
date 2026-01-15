#!/usr/bin/env python3
"""
生成 Fernet 加密密钥用于 ENCRYPTION_KEY 环境变量
"""
try:
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    print("\n" + "="*60)
    print("生成的 ENCRYPTION_KEY（请复制保存）：")
    print("="*60)
    print(key.decode())
    print("="*60)
    print("\n请将此密钥值设置到 Render Dashboard 的 ENCRYPTION_KEY 环境变量中")
    print("="*60 + "\n")
except ImportError:
    print("错误：需要安装 cryptography 模块")
    print("安装命令：pip install cryptography")
    print("\n或者使用在线工具生成 Fernet 密钥")
