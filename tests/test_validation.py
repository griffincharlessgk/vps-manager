import pytest
from unittest.mock import Mock, patch
from core.validation import (
    validate_vps_data,
    validate_account_data,
    validate_bitlaunch_api_data,
    validate_zingproxy_data,
    validate_username,
    validate_password,
    ValidationError
)

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
def sample_bitlaunch_api_data():
    return {
        'api_key': 'test_api_key_123',
        'email': 'test@example.com',
        'update_frequency': 1
    }

@pytest.fixture
def sample_zingproxy_data():
    return {
        'email': 'test@zingproxy.com',
        'password': 'test_access_token_123'
    }

def test_validate_vps_data_success(sample_vps_data):
    result = validate_vps_data(sample_vps_data)
    assert result == sample_vps_data

def test_validate_vps_data_missing_required_fields():
    invalid_data = {
        'id': 'vps1',
        'service': 'ZingProxy'
        # Thiếu name
    }
    
    with pytest.raises(ValidationError, match='Missing required fields: name'):
        validate_vps_data(invalid_data)

def test_validate_vps_data_invalid_ip():
    invalid_data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': 'invalid_ip',
        'expiry': '2024-12-31'
    }
    
    with pytest.raises(ValidationError, match='Invalid IP address format'):
        validate_vps_data(invalid_data)

def test_validate_vps_data_invalid_expiry():
    invalid_data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': '192.168.1.1',
        'expiry': 'invalid_date'
    }
    
    with pytest.raises(ValidationError, match='Invalid expiry date format'):
        validate_vps_data(invalid_data)

def test_validate_account_data_success(sample_account_data):
    result = validate_account_data(sample_account_data)
    assert result == sample_account_data

def test_validate_account_data_missing_required_fields():
    invalid_data = {
        'id': 'acc1',
        'service': 'mail'
        # Thiếu username
    }
    
    with pytest.raises(ValidationError, match='Missing required fields: username'):
        validate_account_data(invalid_data)

def test_validate_account_data_invalid_email():
    invalid_data = {
        'id': 'acc1',
        'service': 'mail',
        'username': 'invalid_email',
        'password': 'secret123',
        'expiry': '2024-12-31'
    }
    
    # Account validation không kiểm tra email format
    result = validate_account_data(invalid_data)
    assert result == invalid_data

def test_validate_account_data_invalid_expiry():
    invalid_data = {
        'id': 'acc1',
        'service': 'mail',
        'username': 'test@example.com',
        'password': 'secret123',
        'expiry': 'invalid_date'
    }
    
    with pytest.raises(ValidationError, match='Invalid expiry date format'):
        validate_account_data(invalid_data)

def test_validate_bitlaunch_api_data_success(sample_bitlaunch_api_data):
    result = validate_bitlaunch_api_data(sample_bitlaunch_api_data)
    assert result == sample_bitlaunch_api_data

def test_validate_bitlaunch_api_data_missing_api_key():
    invalid_data = {
        'email': 'test@example.com',
        'update_frequency': 1
        # Thiếu api_key
    }
    
    with pytest.raises(ValidationError, match='Missing required fields: api_key'):
        validate_bitlaunch_api_data(invalid_data)

def test_validate_bitlaunch_api_data_invalid_email():
    invalid_data = {
        'api_key': 'test_api_key_123',
        'email': 'invalid_email',
        'update_frequency': 1
    }
    
    with pytest.raises(ValidationError, match='Invalid email format'):
        validate_bitlaunch_api_data(invalid_data)

def test_validate_bitlaunch_api_data_invalid_update_frequency():
    invalid_data = {
        'api_key': 'test_api_key_123',
        'email': 'test@example.com',
        'update_frequency': 0  # Phải > 0
    }
    
    with pytest.raises(ValidationError, match='Value must be at least 1'):
        validate_bitlaunch_api_data(invalid_data)

def test_validate_zingproxy_data_success(sample_zingproxy_data):
    result = validate_zingproxy_data(sample_zingproxy_data)
    assert result == sample_zingproxy_data

def test_validate_zingproxy_data_missing_password():
    invalid_data = {
        'email': 'test@zingproxy.com'
        # Thiếu password
    }
    
    with pytest.raises(ValidationError, match='Missing required fields: password'):
        validate_zingproxy_data(invalid_data)

def test_validate_zingproxy_data_invalid_email():
    invalid_data = {
        'email': 'invalid_email',
        'password': 'test_password'
    }
    
    with pytest.raises(ValidationError, match='Invalid email format'):
        validate_zingproxy_data(invalid_data)

def test_validate_username_success():
    result = validate_username('testuser')
    assert result == (True, '')
    assert validate_username('user123') == (True, '')
    assert validate_username('test_user') == (True, '')

def test_validate_username_invalid():
    # Username rỗng
    result = validate_username('')
    assert result == (False, 'Username is required')
    
    # Username quá ngắn
    result = validate_username('ab')
    assert result == (False, 'Username must be at least 3 characters long')
    
    # Username quá dài
    long_username = 'a' * 65
    result = validate_username(long_username)
    assert result == (False, 'Username must be less than 64 characters')
    
    # Username với ký tự không hợp lệ
    result = validate_username('user@name')
    assert result == (False, 'Username can only contain letters, numbers, and underscores')

def test_validate_password_success():
    result = validate_password('password123')
    assert result == (True, '')
    assert validate_password('secret123') == (True, '')
    assert validate_password('MyPass123!') == (True, '')

def test_validate_password_invalid():
    # Password rỗng
    result = validate_password('')
    assert result == (False, 'Password is required')
    
    # Password quá ngắn
    result = validate_password('123')
    assert result == (False, 'Password must be at least 6 characters long')
    
    # Password quá dài
    long_password = 'a' * 129
    result = validate_password(long_password)
    assert result == (False, 'Password must be less than 128 characters')

def test_validate_vps_data_with_optional_fields():
    data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': '192.168.1.1',
        'expiry': '2024-12-31'
    }
    
    result = validate_vps_data(data)
    assert result == data

def test_validate_account_data_with_optional_fields():
    data = {
        'id': 'acc1',
        'service': 'mail',
        'username': 'test@example.com',
        'password': 'secret123',
        'expiry': '2024-12-31'
    }
    
    result = validate_account_data(data)
    assert result == data

def test_validate_vps_data_edge_cases():
    # Test với IP localhost
    data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': '127.0.0.1',
        'expiry': '2024-12-31'
    }
    
    result = validate_vps_data(data)
    assert result['ip'] == '127.0.0.1'
    
    # Test với service rỗng (expect ValidationError)
    data['service'] = ''
    with pytest.raises(ValidationError):
        validate_vps_data(data)

def test_validate_account_data_edge_cases():
    # Test với service rỗng (expect ValidationError)
    data = {
        'id': 'acc1',
        'service': '',
        'username': 'test@example.com',
        'password': 'secret123',
        'expiry': '2024-12-31'
    }
    
    with pytest.raises(ValidationError):
        validate_account_data(data)
    
    # Test với username có dấu gạch dưới
    data['username'] = 'test_user@example.com'
    result = validate_account_data(data)
    assert result['username'] == 'test_user@example.com'

def test_validate_vps_data_without_ip():
    """Test VPS data không có IP (IP là optional)"""
    data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS'
        # Không có IP
    }
    
    result = validate_vps_data(data)
    assert result == data

def test_validate_vps_data_without_expiry():
    """Test VPS data không có expiry (expiry là optional)"""
    data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': '192.168.1.1'
        # Không có expiry
    }
    
    result = validate_vps_data(data)
    assert result == data

def test_validate_account_data_without_expiry():
    """Test Account data không có expiry (expiry là optional)"""
    data = {
        'id': 'acc1',
        'service': 'mail',
        'username': 'test@example.com',
        'password': 'secret123'
        # Không có expiry
    }
    
    result = validate_account_data(data)
    assert result == data

def test_validate_bitlaunch_api_data_without_update_frequency():
    """Test BitLaunch API data không có update_frequency (optional)"""
    data = {
        'api_key': 'test_api_key_123',
        'email': 'test@example.com'
        # Không có update_frequency
    }
    
    result = validate_bitlaunch_api_data(data)
    assert result == data 