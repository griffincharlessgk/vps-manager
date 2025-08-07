from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from core.encryption import encrypt_sensitive_data, decrypt_sensitive_data
from datetime import datetime
import re

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(16), nullable=False)  # 'admin' hoặc 'user'
    notify_days = db.Column(db.Integer, nullable=True, default=3)  # Số ngày trước khi hết hạn để thông báo
    notify_hour = db.Column(db.Integer, nullable=True, default=8)  # Giờ gửi thông báo (0-23)
    notify_minute = db.Column(db.Integer, nullable=True, default=0)  # Phút gửi thông báo (0-59)
    telegram_chat_id = db.Column(db.String, nullable=True)  # Chat ID Telegram riêng
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, ""

class BitLaunchAPI(db.Model):
    __tablename__ = 'bitlaunch_apis'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(128), nullable=False)  # Email từ BitLaunch account
    api_key_encrypted = db.Column(db.String(512), nullable=False)  # API key đã mã hóa
    balance = db.Column(db.Float, nullable=True)  # Số dư hiện tại
    account_limit = db.Column(db.Float, nullable=True)  # Giới hạn
    last_updated = db.Column(db.DateTime, nullable=True)  # Lần cập nhật cuối
    update_frequency = db.Column(db.Integer, nullable=False, default=1)  # Số ngày cập nhật (1, 3, 7, 30)
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # Trạng thái hoạt động
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def api_key(self):
        """Get decrypted API key"""
        return decrypt_sensitive_data(self.api_key_encrypted)

    @api_key.setter
    def api_key(self, value):
        """Set encrypted API key"""
        self.api_key_encrypted = encrypt_sensitive_data(value)

    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

class BitLaunchVPS(db.Model):
    __tablename__ = 'bitlaunch_vps'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, db.ForeignKey('bitlaunch_apis.id'), nullable=False)
    server_id = db.Column(db.Integer, nullable=False)  # ID server từ BitLaunch
    name = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(32), nullable=True)  # running, stopped, etc.
    ip_address = db.Column(db.String(45), nullable=True)  # IP address
    location = db.Column(db.String(64), nullable=True)  # Server location
    plan = db.Column(db.String(64), nullable=True)  # Plan name
    created_at = db.Column(db.DateTime, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=True)

class VPS(db.Model):
    __tablename__ = 'vps'
    id = db.Column(db.String, primary_key=True)
    service = db.Column(db.String)
    name = db.Column(db.String)
    ip = db.Column(db.String)
    expiry = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def validate_expiry(expiry):
        """Validate expiry date format"""
        try:
            datetime.strptime(expiry, '%Y-%m-%d')
            return True
        except ValueError:
            return False

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.String, primary_key=True)
    service = db.Column(db.String)
    username = db.Column(db.String)
    password_encrypted = db.Column(db.String(512), nullable=True)  # Password đã mã hóa
    expiry = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def password(self):
        """Get decrypted password"""
        return decrypt_sensitive_data(self.password_encrypted) if self.password_encrypted else None

    @password.setter
    def password(self, value):
        """Set encrypted password"""
        self.password_encrypted = encrypt_sensitive_data(value) if value else None

class ZingProxyAccount(db.Model):
    __tablename__ = 'zingproxy_accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    access_token_encrypted = db.Column(db.String(512), nullable=False)
    balance = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=True)
    update_frequency = db.Column(db.Integer, nullable=False, default=1)  # Số ngày cập nhật (1, 3, 7, 30)

    @property
    def access_token(self):
        """Get decrypted access token"""
        return decrypt_sensitive_data(self.access_token_encrypted)

    @access_token.setter
    def access_token(self, value):
        """Set encrypted access token"""
        self.access_token_encrypted = encrypt_sensitive_data(value)

class ZingProxy(db.Model):
    __tablename__ = 'zingproxies'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('zingproxy_accounts.id'), nullable=False)
    proxy_id = db.Column(db.String(64), nullable=False)  # id từ API
    ip = db.Column(db.String(64), nullable=True)
    port = db.Column(db.String(16), nullable=True)
    port_socks5 = db.Column(db.String(16), nullable=True)  # Port SOCKS5
    status = db.Column(db.String(32), nullable=True)
    expire_at = db.Column(db.String(32), nullable=True)
    location = db.Column(db.String(64), nullable=True)
    type = db.Column(db.String(32), nullable=True)
    username = db.Column(db.String(128), nullable=True)  # Username cho proxy
    password = db.Column(db.String(128), nullable=True)  # Password cho proxy
    note = db.Column(db.String(256), nullable=True)  # Ghi chú
    created_at = db.Column(db.String(64), nullable=True)  # Thời gian tạo từ API
    auto_renew = db.Column(db.Boolean, nullable=True)  # Tự động gia hạn
    link_change_ip = db.Column(db.String(512), nullable=True)  # Link đổi IP
    last_updated = db.Column(db.DateTime, nullable=True)

class Proxy(db.Model):
    __tablename__ = 'proxies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)  # Tên proxy
    ip = db.Column(db.String(64), nullable=False)
    port = db.Column(db.String(16), nullable=False)
    port_socks5 = db.Column(db.String(16), nullable=True)  # Port SOCKS5 (nếu có)
    username = db.Column(db.String(128), nullable=True)
    password_encrypted = db.Column(db.String(512), nullable=True)  # Password đã mã hóa
    type = db.Column(db.String(32), nullable=True)  # HTTP, HTTPS, SOCKS4, SOCKS5
    location = db.Column(db.String(64), nullable=True)  # Quốc gia/địa điểm
    status = db.Column(db.String(32), default='active')  # active, inactive, expired
    expire_at = db.Column(db.String(32), nullable=True)  # Ngày hết hạn
    source = db.Column(db.String(32), default='manual')  # manual, zingproxy, other
    source_id = db.Column(db.String(64), nullable=True)  # ID từ nguồn gốc (nếu có)
    note = db.Column(db.String(512), nullable=True)  # Ghi chú
    auto_renew = db.Column(db.Boolean, default=False)  # Tự động gia hạn
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def password(self):
        """Get decrypted password"""
        return decrypt_sensitive_data(self.password_encrypted) if self.password_encrypted else None

    @password.setter
    def password(self, value):
        """Set encrypted password"""
        self.password_encrypted = encrypt_sensitive_data(value) if value else None

    @staticmethod
    def validate_ip(ip):
        """Validate IP address format"""
        import re
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(pattern, ip))

    @staticmethod
    def validate_port(port):
        """Validate port number"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except ValueError:
            return False 