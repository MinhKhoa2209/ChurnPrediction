import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    def __init__(self, encryption_key: str):
        try:
            key_bytes = base64.b64decode(encryption_key)
            if len(key_bytes) != 32:
                raise ValueError("Encryption key must be 32 bytes (256 bits)")
            self.aesgcm = AESGCM(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, plaintext: str) -> bytes:
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        nonce = os.urandom(12)

        plaintext_bytes = plaintext.encode("utf-8")
        ciphertext = self.aesgcm.encrypt(nonce, plaintext_bytes, None)

        return nonce + ciphertext

    def decrypt(self, encrypted_data: bytes) -> str:
        if not encrypted_data or len(encrypted_data) < 13:
            raise ValueError("Invalid encrypted data")

        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext_bytes.decode("utf-8")

    def encrypt_optional(self, plaintext: Optional[str]) -> Optional[bytes]:
        if not plaintext or plaintext.strip() == "":
            return None
        return self.encrypt(plaintext)

    def decrypt_optional(self, encrypted_data: Optional[bytes]) -> Optional[str]:
        if not encrypted_data:
            return None
        return self.decrypt(encrypted_data)


def generate_encryption_key() -> str:
    key = AESGCM.generate_key(bit_length=256)
    return base64.b64encode(key).decode("utf-8")
