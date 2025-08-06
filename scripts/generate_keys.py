#!/usr/bin/env python3
"""
Script generate các key cần thiết cho production
"""
import secrets
import string
from cryptography.fernet import Fernet
from datetime import datetime

def generate_secret_key():
    """Generate Flask secret key"""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """Generate encryption key cho sensitive data"""
    return Fernet.generate_key().decode()

def generate_secure_password(length=16):
    """Generate secure password"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

def main():
    print("🔑 VPS Manager - Key Generator")
    print("=" * 40)
    
    # Generate các key
    secret_key = generate_secret_key()
    encryption_key = generate_encryption_key()
    db_password = generate_secure_password(12)
    
    print("✅ Đã generate các key:")
    print(f"SECRET_KEY={secret_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print(f"DB_PASSWORD={db_password}")
    
    print("\n📝 Cập nhật file .env với các giá trị sau:")
    print("=" * 50)
    print(f"SECRET_KEY={secret_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print(f"DATABASE_URL=postgresql://vps_user:{db_password}@localhost/vps_manager")
    print("=" * 50)
    
    print("\n⚠️  Lưu ý:")
    print("- Lưu các key này ở nơi an toàn")
    print("- Không chia sẻ các key này")
    print("- Backup các key để khôi phục khi cần")
    
    # Tạo file backup keys
    backup_content = f"""# VPS Manager - Production Keys
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SECRET_KEY={secret_key}
ENCRYPTION_KEY={encryption_key}
DB_PASSWORD={db_password}

# PostgreSQL Setup Commands:
# CREATE USER vps_user WITH PASSWORD '{db_password}';
# CREATE DATABASE vps_manager OWNER vps_user;
# GRANT ALL PRIVILEGES ON DATABASE vps_manager TO vps_user;
"""
    
    with open('production_keys_backup.txt', 'w') as f:
        f.write(backup_content)
    
    print(f"\n💾 Đã backup keys vào file: production_keys_backup.txt")
    print("⚠️  Xóa file này sau khi đã cập nhật .env!")

if __name__ == '__main__':
    main() 