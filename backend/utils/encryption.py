"""
Encryption Utilities
Requirement 23.1: AES-256-GCM encryption for sensitive fields

This module provides encryption and decryption functions for sensitive customer data.
"""

import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    """Service for encrypting and decrypting sensitive data using AES-256-GCM"""
    
    def __init__(self, encryption_key: str):
        """
        Initialize encryption service with a key
        
        Args:
            encryption_key: Base64-encoded 32-byte encryption key
        """
        # Decode the base64 key
        try:
            key_bytes = base64.b64decode(encryption_key)
            if len(key_bytes) != 32:
                raise ValueError("Encryption key must be 32 bytes (256 bits)")
            self.aesgcm = AESGCM(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")
    
    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt a plaintext string using AES-256-GCM
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted bytes (nonce + ciphertext + tag)
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
        
        # Generate a random 96-bit nonce (12 bytes is recommended for GCM)
        nonce = os.urandom(12)
        
        # Encrypt the plaintext
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext = self.aesgcm.encrypt(nonce, plaintext_bytes, None)
        
        # Return nonce + ciphertext (the ciphertext already includes the auth tag)
        return nonce + ciphertext
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypt encrypted data using AES-256-GCM
        
        Args:
            encrypted_data: Encrypted bytes (nonce + ciphertext + tag)
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted_data or len(encrypted_data) < 13:  # 12 bytes nonce + at least 1 byte data
            raise ValueError("Invalid encrypted data")
        
        # Extract nonce and ciphertext
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        # Decrypt
        plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
        
        return plaintext_bytes.decode('utf-8')
    
    def encrypt_optional(self, plaintext: Optional[str]) -> Optional[bytes]:
        """
        Encrypt an optional string (returns None if input is None or empty)
        
        Args:
            plaintext: Optional string to encrypt
            
        Returns:
            Encrypted bytes or None
        """
        if not plaintext or plaintext.strip() == "":
            return None
        return self.encrypt(plaintext)
    
    def decrypt_optional(self, encrypted_data: Optional[bytes]) -> Optional[str]:
        """
        Decrypt optional encrypted data (returns None if input is None)
        
        Args:
            encrypted_data: Optional encrypted bytes
            
        Returns:
            Decrypted string or None
        """
        if not encrypted_data:
            return None
        return self.decrypt(encrypted_data)


def generate_encryption_key() -> str:
    """
    Generate a new random 256-bit encryption key
    
    Returns:
        Base64-encoded encryption key
    """
    key = AESGCM.generate_key(bit_length=256)
    return base64.b64encode(key).decode('utf-8')


# Example usage for generating a key:
# python -c "from backend.utils.encryption import generate_encryption_key; print(generate_encryption_key())"
