"""
Encryption service for API keys using Fernet symmetric encryption
"""
from cryptography.fernet import Fernet
from django.conf import settings
import os


def get_encryption_key():
    """
    Get or generate encryption key from environment
    
    Returns:
        bytes: Fernet encryption key
    """
    key = os.getenv('ENCRYPTION_KEY')
    
    if not key:
        # Generate a new key if not set (for development)
        # In production, this should be set in environment variables
        key = Fernet.generate_key().decode()
    
    return key.encode() if isinstance(key, str) else key


def get_cipher():
    """
    Get Fernet cipher instance
    
    Returns:
        Fernet: Cipher instance for encryption/decryption
    """
    key = get_encryption_key()
    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for secure storage

    
    Args:
        api_key: Plain text API key
        
    Returns:
        str: Encrypted API key (base64 encoded)
    """
    if not api_key:
        return ""
    
    cipher = get_cipher()
    encrypted = cipher.encrypt(api_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key for use in API calls
    
    Args:
        encrypted_key: Encrypted API key (base64 encoded)
        
    Returns:
        str: Plain text API key
    """
    if not encrypted_key:
        return ""
    
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_key.encode())
    return decrypted.decode()


def mask_api_key(api_key: str) -> str:
    """
    Mask an API key for display (show only first 3 and last 3 characters)
    
    Args:
        api_key: Plain text or encrypted API key
        
    Returns:

        str: Masked API key (e.g., "sk-...xyz")
    """
    if not api_key or len(api_key) < 6:
        return "***"
    
    return f"{api_key[:3]}...{api_key[-3:]}"
