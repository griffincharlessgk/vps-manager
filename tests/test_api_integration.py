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
        # Tạo database test
        from core.models import db
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers():
    return {'Content-Type': 'application/json'}

@pytest.fixture
def sample_user():
    user = User(username='testuser', role='user')
    user.set_password('testpass123')
    return user

@pytest.fixture
def sample_admin():
    admin = User(username='admin', role='admin')
    admin.set_password('adminpass123')
    return admin

def test_home_redirect(client):
    """Test trang chủ redirect về login"""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location

def test_login_page(client):
    """Test trang login hiển thị"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login_success(client, app, sample_user):
    """Test đăng nhập thành công"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'

def test_login_invalid_credentials(client):
    """Test đăng nhập với thông tin sai"""
    response = client.post('/login', json={
        'username': 'wronguser',
        'password': 'wrongpass'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['status'] == 'error'

def test_vps_api_requires_auth(client):
    """Test API VPS yêu cầu đăng nhập"""
    response = client.get('/api/vps')
    assert response.status_code == 401

def test_accounts_api_requires_auth(client):
    """Test API Accounts yêu cầu đăng nhập"""
    response = client.get('/api/accounts')
    assert response.status_code == 401

@patch('core.manager.list_vps')
def test_vps_api_with_auth(mock_list_vps, client, app, sample_user):
    """Test API VPS khi đã đăng nhập"""
    mock_list_vps.return_value = [
        {'id': 'vps1', 'name': 'Test VPS', 'ip': '192.168.1.1'}
    ]
    
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test API VPS
    response = client.get('/api/vps')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'Test VPS'

@patch('core.manager.list_accounts')
def test_accounts_api_with_auth(mock_list_accounts, client, app, sample_user):
    """Test API Accounts khi đã đăng nhập"""
    mock_list_accounts.return_value = [
        {'id': 'acc1', 'username': 'test@example.com', 'service': 'mail'}
    ]
    
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test API Accounts
    response = client.get('/api/accounts')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['username'] == 'test@example.com'

def test_add_vps_api(client, app, sample_user):
    """Test API thêm VPS"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm VPS
    vps_data = {
        'id': 'vps1',
        'service': 'Test',
        'name': 'Test VPS',
        'ip': '192.168.1.1',
        'expiry': '2024-12-31'
    }
    
    with patch('core.manager.add_vps') as mock_add_vps:
        mock_add_vps.return_value = None
        response = client.post('/api/vps', json=vps_data)
        assert response.status_code == 201

def test_add_account_api(client, app, sample_user):
    """Test API thêm Account"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test thêm Account
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

def test_bitlaunch_api_requires_auth(client):
    """Test API BitLaunch yêu cầu đăng nhập"""
    response = client.get('/api/bitlaunch-apis')
    assert response.status_code == 401

def test_zingproxy_api_requires_auth(client):
    """Test API ZingProxy yêu cầu đăng nhập"""
    response = client.get('/api/zingproxy-accounts')
    assert response.status_code == 401

def test_cloudfly_api_requires_auth(client):
    """Test API CloudFly yêu cầu đăng nhập"""
    response = client.get('/api/cloudfly/apis')
    assert response.status_code == 401

def test_rocket_chat_api_requires_auth(client):
    """Test API Rocket Chat yêu cầu đăng nhập"""
    response = client.get('/api/rocket-chat/config')
    assert response.status_code == 401

def test_scheduler_api_requires_auth(client):
    """Test API Scheduler yêu cầu đăng nhập"""
    response = client.get('/api/scheduler/status')
    assert response.status_code == 401

def test_admin_only_apis(client, app, sample_user):
    """Test các API chỉ dành cho admin"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập với user thường
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test API users (chỉ admin)
    response = client.get('/api/users')
    assert response.status_code == 403

def test_admin_apis_with_admin_user(client, app, sample_admin):
    """Test các API admin với user admin"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_admin)
        db.session.commit()
    
    # Đăng nhập với admin
    client.post('/login', json={
        'username': 'admin',
        'password': 'adminpass123'
    })
    
    # Test API users
    response = client.get('/api/users')
    assert response.status_code == 200

def test_logout_api(client, app, sample_user):
    """Test API logout"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test logout
    response = client.post('/logout')
    assert response.status_code == 200
    data = response.get_json()
    assert data['msg'] == 'Đã đăng xuất'

def test_me_api(client, app, sample_user):
    """Test API /me để lấy thông tin user hiện tại"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test API /me
    response = client.get('/me')
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'testuser'
    assert data['role'] == 'user'

def test_expiry_warnings_api(client):
    """Test API expiry warnings (không yêu cầu đăng nhập)"""
    response = client.get('/api/expiry-warnings')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'warnings' in data

def test_404_error_handler(client):
    """Test 404 error handler"""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Not found'

def test_500_error_handler(client, app):
    """Test 500 error handler"""
    with app.app_context():
        from core.models import db
        
        # Tạo route test để gây lỗi
        @app.route('/test-error')
        def test_error():
            raise Exception('Test error')
        
        # Test route gây lỗi
        response = client.get('/test-error')
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Internal server error' 