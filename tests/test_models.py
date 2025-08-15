import pytest
from datetime import datetime, timedelta
from core.models import (
    db, User, VPS, Account, CloudFlyAPI, CloudFlyVPS,
    ZingProxyAccount, RocketChatConfig
)
from werkzeug.security import check_password_hash

@pytest.fixture
def sample_user_data():
    return {
        'username': 'testuser',
        'password': 'testpass123',
        'role': 'user'
    }

@pytest.fixture
def sample_vps_data():
    return {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': '192.168.1.1',
        'expiry': '2024-12-31'
    }

@pytest.fixture
def sample_account_data():
    return {
        'id': 'acc1',
        'service': 'mail',
        'username': 'test@example.com',
        'password': 'secret123',
        'expiry': '2024-12-31'
    }

@pytest.fixture
def sample_cloudfly_api_data():
    return {
        'user_id': 1,
        'email': 'test@cloudfly.vn',
        'api_token': 'test_token_123',
        'balance': 100000,
        'account_limit': 0,
        'update_frequency': 1
    }

@pytest.fixture
def sample_rocket_chat_config_data():
    return {
        'user_id': 1,
        'auth_token': 'test_auth_token',
        'user_id_rocket': 'test_rocket_user',
        'room_id': 'test_room_id',
        'room_name': 'Test Room'
    }

def test_user_creation(sample_user_data):
    user = User(
        username=sample_user_data['username'],
        role=sample_user_data['role']
    )
    user.set_password(sample_user_data['password'])
    
    assert user.username == sample_user_data['username']
    assert user.role == sample_user_data['role']
    assert check_password_hash(user.password_hash, sample_user_data['password'])

def test_user_password_validation(sample_user_data):
    user = User(
        username=sample_user_data['username'],
        role=sample_user_data['role']
    )
    user.set_password(sample_user_data['password'])
    
    assert user.check_password(sample_user_data['password']) is True
    assert user.check_password('wrong_password') is False

def test_user_password_length_validation():
    user = User(username='testuser', role='user')
    
    # Password quá ngắn
    with pytest.raises(ValueError, match='Password must be at least 6 characters long'):
        user.set_password('123')
    
    # Password hợp lệ
    user.set_password('123456')
    assert user.check_password('123456') is True

def test_vps_creation(sample_vps_data):
    vps = VPS(
        id=sample_vps_data['id'],
        service=sample_vps_data['service'],
        name=sample_vps_data['name'],
        ip=sample_vps_data['ip'],
        expiry=sample_vps_data['expiry']
    )
    
    assert vps.id == sample_vps_data['id']
    assert vps.service == sample_vps_data['service']
    assert vps.name == sample_vps_data['name']
    assert vps.ip == sample_vps_data['ip']
    assert vps.expiry == sample_vps_data['expiry']

def test_account_creation(sample_account_data):
    account = Account(
        id=sample_account_data['id'],
        service=sample_account_data['service'],
        username=sample_account_data['username'],
        password=sample_account_data['password'],
        expiry=sample_account_data['expiry']
    )
    
    assert account.id == sample_account_data['id']
    assert account.service == sample_account_data['service']
    assert account.username == sample_account_data['username']
    assert account.password == sample_account_data['password']
    assert account.expiry == sample_account_data['expiry']

def test_cloudfly_api_creation(sample_cloudfly_api_data):
    api = CloudFlyAPI(
        user_id=sample_cloudfly_api_data['user_id'],
        email=sample_cloudfly_api_data['email'],
        api_token=sample_cloudfly_api_data['api_token'],
        balance=sample_cloudfly_api_data['balance'],
        account_limit=sample_cloudfly_api_data['account_limit'],
        update_frequency=sample_cloudfly_api_data['update_frequency']
    )
    
    assert api.user_id == sample_cloudfly_api_data['user_id']
    assert api.email == sample_cloudfly_api_data['email']
    assert api.api_token == sample_cloudfly_api_data['api_token']
    assert api.balance == sample_cloudfly_api_data['balance']
    assert api.account_limit == sample_cloudfly_api_data['account_limit']
    assert api.update_frequency == sample_cloudfly_api_data['update_frequency']

def test_cloudfly_vps_creation():
    vps = CloudFlyVPS(
        api_id=1,
        instance_id='instance_123',
        name='CloudFly VPS',
        status='running',
        ip_address='192.168.1.100',
        region='HN-Cloud01',
        image_name='CentOS-7.9',
        flavor_type='Standard',
        ram=1,
        vcpus=1,
        disk=20
    )
    
    assert vps.api_id == 1
    assert vps.instance_id == 'instance_123'
    assert vps.name == 'CloudFly VPS'
    assert vps.status == 'running'
    assert vps.ip_address == '192.168.1.100'
    assert vps.region == 'HN-Cloud01'
    assert vps.image_name == 'CentOS-7.9'
    assert vps.flavor_type == 'Standard'
    assert vps.ram == 1
    assert vps.vcpus == 1
    assert vps.disk == 20

def test_zingproxy_account_creation():
    account = ZingProxyAccount(
        user_id=1,
        email='test@zingproxy.com',
        access_token='test_access_token',
        balance=50000,
        update_frequency=1
    )
    
    assert account.user_id == 1
    assert account.email == 'test@zingproxy.com'
    assert account.access_token == 'test_access_token'
    assert account.balance == 50000
    assert account.update_frequency == 1

def test_rocket_chat_config_creation(sample_rocket_chat_config_data):
    config = RocketChatConfig(
        user_id=sample_rocket_chat_config_data['user_id'],
        auth_token=sample_rocket_chat_config_data['auth_token'],
        user_id_rocket=sample_rocket_chat_config_data['user_id_rocket'],
        room_id=sample_rocket_chat_config_data['room_id'],
        room_name=sample_rocket_chat_config_data['room_name']
    )
    
    assert config.user_id == sample_rocket_chat_config_data['user_id']
    assert config.auth_token == sample_rocket_chat_config_data['auth_token']
    assert config.user_id_rocket == sample_rocket_chat_config_data['user_id_rocket']
    assert config.room_id == sample_rocket_chat_config_data['room_id']
    assert config.room_name == sample_rocket_chat_config_data['room_name']

def test_rocket_chat_config_validation():
    # Test room_id validation
    assert RocketChatConfig.validate_room_id('valid_room_id_123') is True
    assert RocketChatConfig.validate_room_id('short') is False
    assert RocketChatConfig.validate_room_id('') is False
    
    # Test user_id_rocket validation - 'short' có 5 ký tự nên pass validation
    assert RocketChatConfig.validate_user_id_rocket('valid_user_id_123') is True
    assert RocketChatConfig.validate_user_id_rocket('short') is True  # 5 ký tự >= 5
    assert RocketChatConfig.validate_user_id_rocket('tiny') is False  # 4 ký tự < 5
    assert RocketChatConfig.validate_user_id_rocket('') is False

def test_user_role_validation():
    # Role hợp lệ
    user = User(username='admin', role='admin')
    assert user.role == 'admin'
    
    user = User(username='user', role='user')
    assert user.role == 'user'
    
    # Role mặc định - User model không có default role
    user = User(username='default')
    assert user.role is None

def test_user_telegram_settings():
    user = User(username='testuser', role='user')
    
    # Test telegram_chat_id
    user.telegram_chat_id = '123456789'
    assert user.telegram_chat_id == '123456789'
    
    # Test notify_days
    user.notify_days = 7
    assert user.notify_days == 7
    
    # Test notify_hour và notify_minute
    user.notify_hour = 9
    user.notify_minute = 30
    assert user.notify_hour == 9
    assert user.notify_minute == 30

def test_vps_expiry_validation():
    # Ngày hợp lệ
    vps = VPS(
        id='vps1',
        service='Test',
        name='Test VPS',
        ip='192.168.1.1',
        expiry='2024-12-31'
    )
    assert vps.expiry == '2024-12-31'
    
    # Test validation function
    assert VPS.validate_expiry('2024-12-31') is True
    assert VPS.validate_expiry('invalid_date') is False

def test_account_expiry_validation():
    # Ngày hợp lệ
    account = Account(
        id='acc1',
        service='Test',
        username='test@example.com',
        password='secret123',
        expiry='2024-12-31'
    )
    assert account.expiry == '2024-12-31'
    
    # Account model không có validation function riêng
    # Sử dụng VPS validation function
    assert VPS.validate_expiry('2024-12-31') is True
    assert VPS.validate_expiry('invalid_date') is False

def test_model_timestamps():
    user = User(username='testuser', role='user')
    
    # Kiểm tra created_at - sẽ được set khi commit
    assert user.created_at is None  # Chưa commit nên chưa có timestamp
    
    # Kiểm tra updated_at - sẽ được set khi commit
    assert user.updated_at is None  # Chưa commit nên chưa có timestamp

def test_model_string_representations():
    user = User(username='testuser', role='user')
    # User model không có __str__ method tùy chỉnh
    # Sẽ sử dụng SQLAlchemy default representation
    user_str = str(user)
    assert 'User' in user_str
    assert 'transient' in user_str
    
    vps = VPS(
        id='vps1',
        service='Test',
        name='Test VPS',
        ip='192.168.1.1',
        expiry='2024-12-31'
    )
    # VPS model không có __str__ method tùy chỉnh
    vps_str = str(vps)
    assert 'VPS' in vps_str
    
    account = Account(
        id='acc1',
        service='Test',
        username='test@example.com',
        password='secret123',
        expiry='2024-12-31'
    )
    # Account model không có __str__ method tùy chỉnh
    account_str = str(account)
    assert 'Account' in account_str

def test_user_username_validation():
    # Test username validation
    assert User.validate_username('validuser') == (True, '')
    assert User.validate_username('user123') == (True, '')
    assert User.validate_username('test_user') == (True, '')
    
    # Test username quá ngắn
    assert User.validate_username('ab') == (False, 'Username must be at least 3 characters long')
    
    # Test username với ký tự không hợp lệ
    assert User.validate_username('user@name') == (False, 'Username can only contain letters, numbers, and underscores')

def test_bitlaunch_api_email_validation():
    from core.models import BitLaunchAPI
    # Test email validation
    assert BitLaunchAPI.validate_email('test@example.com') is True
    assert BitLaunchAPI.validate_email('user@domain.co.uk') is True
    
    # Test email không hợp lệ
    assert BitLaunchAPI.validate_email('invalid_email') is False
    assert BitLaunchAPI.validate_email('user@') is False
    assert BitLaunchAPI.validate_email('@domain.com') is False

def test_cloudfly_api_email_validation():
    from core.models import CloudFlyAPI
    # Test email validation
    assert CloudFlyAPI.validate_email('test@cloudfly.vn') is True
    assert CloudFlyAPI.validate_email('user@domain.com') is True
    
    # Test email không hợp lệ
    assert CloudFlyAPI.validate_email('invalid_email') is False
    assert CloudFlyAPI.validate_email('user@') is False
    assert CloudFlyAPI.validate_email('@domain.com') is False

def test_proxy_ip_validation():
    from core.models import Proxy
    
    # Test IP validation
    assert Proxy.validate_ip('192.168.1.1') is True
    assert Proxy.validate_ip('10.0.0.1') is True
    assert Proxy.validate_ip('172.16.0.1') is True
    
    # Test IP không hợp lệ
    assert Proxy.validate_ip('invalid_ip') is False
    assert Proxy.validate_ip('256.1.2.3') is False
    assert Proxy.validate_ip('192.168.1') is False

def test_proxy_port_validation():
    from core.models import Proxy
    
    # Test port validation
    assert Proxy.validate_port('80') is True
    assert Proxy.validate_port('443') is True
    assert Proxy.validate_port('8080') is True
    assert Proxy.validate_port('1') is True
    assert Proxy.validate_port('65535') is True
    
    # Test port không hợp lệ
    assert Proxy.validate_port('0') is False
    assert Proxy.validate_port('65536') is False
    assert Proxy.validate_port('invalid') is False 