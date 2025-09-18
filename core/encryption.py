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
        """Lấy hoặc tạo encryption key từ environment variable và chuẩn hóa format.
        - Hỗ trợ các trường hợp: key base64 44 ký tự, key base64 thiếu padding, hoặc bytes 32 chiều dài.
        - Nếu không hợp lệ: tự sinh key mới.
        - Luôn set lại os.environ['ENCRYPTION_KEY'] bằng key chuẩn hóa để lần sau không cảnh báo.
        """
        raw = os.getenv('ENCRYPTION_KEY')
        key: bytes
        if not raw:
            key = Fernet.generate_key()
            logger.warning("ENCRYPTION_KEY not found. Generated a new key for this runtime.")
            logger.warning("Set ENCRYPTION_KEY in environment for persistence.")
        else:
            try:
                if isinstance(raw, bytes):
                    # If bytes provided: if already 44-char base64 bytes, try decode
                    try:
                        decoded = base64.urlsafe_b64decode(raw)
                        if len(decoded) != 32:
                            raise ValueError("decoded length != 32 bytes")
                        key = base64.urlsafe_b64encode(decoded)
                    except Exception:
                        # Treat as raw 32 bytes
                        if len(raw) == 32:
                            key = base64.urlsafe_b64encode(raw)
                        else:
                            raise ValueError("bytes key must be 32 bytes or base64 of 32 bytes")
                else:
                    # str input: normalize padding and decode
                    s = raw.strip()
                    pad = '=' * ((4 - (len(s) % 4)) % 4)
                    decoded = base64.urlsafe_b64decode(s + pad)
                    if len(decoded) != 32:
                        raise ValueError("decoded length != 32 bytes")
                    key = base64.urlsafe_b64encode(decoded)
                if raw != key and isinstance(raw, (str, bytes)):
                    logger.info("Normalized ENCRYPTION_KEY format for this runtime.")
            except Exception as e:
                logger.warning(f"Invalid ENCRYPTION_KEY format: {e}. Generating new key.")
                key = Fernet.generate_key()
        # Persist normalized key in environment for current process
        try:
            os.environ['ENCRYPTION_KEY'] = key.decode() if isinstance(key, (bytes, bytearray)) else str(key)
        except Exception:
            pass
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