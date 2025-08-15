import pytest
from unittest.mock import Mock, patch
from ui.app import create_app
from core.models import User, VPS, Account

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        from core.models import db
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_user():
    user = User(username='testuser', role='user')
    user.set_password('testpass123')
    return user

def test_vps_form_validation_success(client, app, sample_user):
    """Test VPS form validation thành công"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm VPS với dữ liệu hợp lệ
    vps_data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': '192.168.1.1',
        'expiry': '2024-12-31'
    }
    
    with patch('core.manager.add_vps') as mock_add_vps:
        mock_add_vps.return_value = None
        response = client.post('/api/vps', json=vps_data)
        assert response.status_code == 201

def test_vps_form_validation_missing_fields(client, app, sample_user):
    """Test VPS form validation thiếu fields bắt buộc"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm VPS thiếu fields
    invalid_vps_data = {
        'id': 'vps1',
        'service': 'ZingProxy'
        # Thiếu name, ip, expiry
    }
    
    response = client.post('/api/vps', json=invalid_vps_data)
    assert response.status_code == 400

def test_vps_form_validation_invalid_ip(client, app, sample_user):
    """Test VPS form validation IP không hợp lệ"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm VPS với IP không hợp lệ
    invalid_vps_data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': 'invalid_ip',
        'expiry': '2024-12-31'
    }
    
    response = client.post('/api/vps', json=invalid_vps_data)
    assert response.status_code == 400

def test_vps_form_validation_invalid_expiry(client, app, sample_user):
    """Test VPS form validation expiry không hợp lệ"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm VPS với expiry không hợp lệ
    invalid_vps_data = {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'Test VPS',
        'ip': '192.168.1.1',
        'expiry': 'invalid_date'
    }
    
    response = client.post('/api/vps', json=invalid_vps_data)
    assert response.status_code == 400

def test_account_form_validation_success(client, app, sample_user):
    """Test Account form validation thành công"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Account với dữ liệu hợp lệ
    account_data = {
        'id': 'acc1',
        'service': 'mail',
        'username': 'test@example.com',
        'password': 'secret123',
        'expiry': '2024-12-31'
    }
    
    with patch('core.manager.add_account') as mock_add_account:
        mock_add_account.return_value = None
        response = client.post('/api/accounts', json=account_data)
        assert response.status_code == 201

def test_account_form_validation_missing_fields(client, app, sample_user):
    """Test Account form validation thiếu fields bắt buộc"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Account thiếu fields
    invalid_account_data = {
        'id': 'acc1',
        'service': 'mail'
        # Thiếu username, password, expiry
    }
    
    response = client.post('/api/accounts', json=invalid_account_data)
    assert response.status_code == 400

def test_account_form_validation_invalid_expiry(client, app, sample_user):
    """Test Account form validation expiry không hợp lệ"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Account với expiry không hợp lệ
    invalid_account_data = {
        'id': 'acc1',
        'service': 'mail',
        'username': 'test@example.com',
        'password': 'secret123',
        'expiry': 'invalid_date'
    }
    
    response = client.post('/api/accounts', json=invalid_account_data)
    assert response.status_code == 400

def test_bitlaunch_api_form_validation_success(client, app, sample_user):
    """Test BitLaunch API form validation thành công"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm BitLaunch API với dữ liệu hợp lệ
    api_data = {
        'api_key': 'test_api_key_123',
        'email': 'test@example.com',
        'update_frequency': 1
    }
    
    with patch('core.manager.add_bitlaunch_api') as mock_add_api:
        mock_add_api.return_value = None
        response = client.post('/api/bitlaunch-apis', json=api_data)
        assert response.status_code == 201

def test_bitlaunch_api_form_validation_missing_api_key(client, app, sample_user):
    """Test BitLaunch API form validation thiếu API key"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm BitLaunch API thiếu API key
    invalid_api_data = {
        'email': 'test@example.com',
        'update_frequency': 1
    }
    
    response = client.post('/api/bitlaunch-apis', json=invalid_api_data)
    assert response.status_code == 400

def test_bitlaunch_api_form_validation_invalid_email(client, app, sample_user):
    """Test BitLaunch API form validation email không hợp lệ"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm BitLaunch API với email không hợp lệ
    invalid_api_data = {
        'api_key': 'test_api_key_123',
        'email': 'invalid_email',
        'update_frequency': 1
    }
    
    response = client.post('/api/bitlaunch-apis', json=invalid_api_data)
    assert response.status_code == 400

def test_zingproxy_form_validation_success(client, app, sample_user):
    """Test ZingProxy form validation thành công"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm ZingProxy account với dữ liệu hợp lệ
    account_data = {
        'access_token': 'test_access_token_123',
        'email': 'test@zingproxy.com',
        'update_frequency': 1
    }
    
    with patch('core.manager.add_zingproxy_account') as mock_add_account:
        mock_add_account.return_value = None
        response = client.post('/api/zingproxy-accounts', json=account_data)
        assert response.status_code == 201

def test_zingproxy_form_validation_missing_token(client, app, sample_user):
    """Test ZingProxy form validation thiếu access token"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm ZingProxy account thiếu access token
    invalid_account_data = {
        'email': 'test@zingproxy.com',
        'update_frequency': 1
    }
    
    response = client.post('/api/zingproxy-accounts', json=invalid_account_data)
    assert response.status_code == 400

def test_cloudfly_form_validation_success(client, app, sample_user):
    """Test CloudFly form validation thành công"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm CloudFly API với dữ liệu hợp lệ
    api_data = {
        'api_token': 'test_token_123',
        'update_frequency': 1
    }
    
    with patch('core.manager.add_cloudfly_api') as mock_add_api:
        mock_add_api.return_value = None
        response = client.post('/api/cloudfly/apis', json=api_data)
        assert response.status_code == 201

def test_cloudfly_form_validation_missing_token(client, app, sample_user):
    """Test CloudFly form validation thiếu API token"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm CloudFly API thiếu API token
    invalid_api_data = {
        'update_frequency': 1
    }
    
    response = client.post('/api/cloudfly/apis', json=invalid_api_data)
    assert response.status_code == 400

def test_rocket_chat_form_validation_success(client, app, sample_user):
    """Test Rocket Chat form validation thành công"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Rocket Chat config với dữ liệu hợp lệ
    config_data = {
        'auth_token': 'test_auth_token',
        'user_id_rocket': 'test_rocket_user',
        'room_id': 'test_room_id_123',
        'room_name': 'Test Room'
    }
    
    with patch('core.manager.add_rocket_chat_config') as mock_add_config:
        mock_add_config.return_value = None
        response = client.post('/api/rocket-chat/config', json=config_data)
        assert response.status_code == 201

def test_rocket_chat_form_validation_missing_fields(client, app, sample_user):
    """Test Rocket Chat form validation thiếu fields bắt buộc"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Rocket Chat config thiếu fields
    invalid_config_data = {
        'auth_token': 'test_auth_token'
        # Thiếu user_id_rocket, room_id
    }
    
    response = client.post('/api/rocket-chat/config', json=invalid_config_data)
    assert response.status_code == 400

def test_user_form_validation_success(client, app, sample_admin):
    """Test User form validation thành công (admin only)"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_admin)
        db.session.commit()
    
    # Đăng nhập với admin
    client.post('/login', json={
        'username': 'admin',
        'password': 'adminpass123'
    })
    
    # Test thêm User với dữ liệu hợp lệ
    user_data = {
        'username': 'newuser',
        'password': 'newpass123',
        'role': 'user'
    }
    
    with patch('core.manager.add_user') as mock_add_user:
        mock_add_user.return_value = None
        response = client.post('/api/users', json=user_data)
        assert response.status_code == 201

def test_user_form_validation_short_password(client, app, sample_admin):
    """Test User form validation password quá ngắn (admin only)"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_admin)
        db.session.commit()
    
    # Đăng nhập với admin
    client.post('/login', json={
        'username': 'admin',
        'password': 'adminpass123'
    })
    
    # Test thêm User với password quá ngắn
    invalid_user_data = {
        'username': 'newuser',
        'password': '123',  # Quá ngắn
        'role': 'user'
    }
    
    response = client.post('/api/users', json=invalid_user_data)
    assert response.status_code == 400

def test_user_form_validation_invalid_role(client, app, sample_admin):
    """Test User form validation role không hợp lệ (admin only)"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_admin)
        db.session.commit()
    
    # Đăng nhập với admin
    client.post('/login', json={
        'username': 'admin',
        'password': 'adminpass123'
    })
    
    # Test thêm User với role không hợp lệ
    invalid_user_data = {
        'username': 'newuser',
        'password': 'newpass123',
        'role': 'invalid_role'
    }
    
    response = client.post('/api/users', json=invalid_user_data)
    assert response.status_code == 400

def test_proxy_form_validation_success(client, app, sample_user):
    """Test Proxy form validation thành công"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Proxy với dữ liệu hợp lệ
    proxy_data = {
        'name': 'Test Proxy',
        'ip': '192.168.1.100',
        'port': '8080',
        'type': 'HTTP',
        'location': 'Vietnam'
    }
    
    with patch('core.manager.add_proxy') as mock_add_proxy:
        mock_add_proxy.return_value = None
        response = client.post('/api/proxies', json=proxy_data)
        assert response.status_code == 201

def test_proxy_form_validation_invalid_ip(client, app, sample_user):
    """Test Proxy form validation IP không hợp lệ"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Proxy với IP không hợp lệ
    invalid_proxy_data = {
        'name': 'Test Proxy',
        'ip': 'invalid_ip',
        'port': '8080',
        'type': 'HTTP',
        'location': 'Vietnam'
    }
    
    response = client.post('/api/proxies', json=invalid_proxy_data)
    assert response.status_code == 400

def test_proxy_form_validation_invalid_port(client, app, sample_user):
    """Test Proxy form validation port không hợp lệ"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Proxy với port không hợp lệ
    invalid_proxy_data = {
        'name': 'Test Proxy',
        'ip': '192.168.1.100',
        'port': '99999',  # Port không hợp lệ
        'type': 'HTTP',
        'location': 'Vietnam'
    }
    
    response = client.post('/api/proxies', json=invalid_proxy_data)
    assert response.status_code == 400 