import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Lấy hoặc tạo encryption key từ environment variable"""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            # Tạo key mới nếu chưa có
            key = Fernet.generate_key()
            logger.warning("ENCRYPTION_KEY not found in environment. Generated new key.")
            logger.warning("Please set ENCRYPTION_KEY environment variable for production.")
        else:
            # Nếu key được cung cấp, đảm bảo nó đúng format
            try:
                # Thử decode để kiểm tra format
                if isinstance(key, str):
                    # Nếu là string, thử decode base64
                    key_bytes = base64.urlsafe_b64decode(key + '=' * (4 - len(key) % 4))
                    if len(key_bytes) != 32:
                        raise ValueError("Key must be 32 bytes when decoded")
                    key = base64.urlsafe_b64encode(key_bytes)
                else:
                    # Nếu đã là bytes, encode thành base64
                    key = base64.urlsafe_b64encode(key)
            except Exception as e:
                logger.warning(f"Invalid ENCRYPTION_KEY format: {e}. Generating new key.")
                key = Fernet.generate_key()
        
        return key
    
    def encrypt(self, data: str) -> str:
        """Mã hóa dữ liệu"""
        if not data:
            return data
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return data
    
    def decrypt(self, encrypted_data: str) -> str:
        """Giải mã dữ liệu"""
        if not encrypted_data:
            return encrypted_data
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return encrypted_data

# Global encryption manager instance
encryption_manager = EncryptionManager()

def encrypt_sensitive_data(data: str) -> str:
    """Wrapper function để mã hóa dữ liệu nhạy cảm"""
    return encryption_manager.encrypt(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Wrapper function để giải mã dữ liệu nhạy cảm"""
    return encryption_manager.decrypt(encrypted_data) 