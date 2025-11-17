# app/utils/encryption.py
from cryptography.fernet import Fernet
import os
import base64

class CredentialEncryption:
    """Utility for encrypting/decrypting API keys and secrets"""

    def __init__(self):
        # Use JWT_SECRET_KEY as the encryption key (ensure it's 32 bytes URL-safe base64-encoded)
        secret = os.getenv("JWT_SECRET_KEY", "")

        if not secret:
            raise ValueError("JWT_SECRET_KEY not set in environment")

        # Derive a Fernet key from the JWT secret
        # Fernet requires a 32-byte key encoded in base64
        key_bytes = secret.encode()[:32].ljust(32, b'0')  # Ensure 32 bytes
        self.key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string (like an API key)
        Returns base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string
        Returns plaintext string
        """
        if not encrypted_text:
            return ""

        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            # If decryption fails, return empty string (corrupted data)
            print(f"Decryption error: {e}")
            return ""

# Global instance
credential_encryption = CredentialEncryption()
