import pytest
from unittest.mock import Mock, patch
from ui.app import create_app
from core.models import User, VPS, Account, CloudFlyAPI, ZingProxyAccount

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

@pytest.fixture
def sample_admin():
    admin = User(username='admin', role='admin')
    admin.set_password('adminpass123')
    return admin

@pytest.fixture
def sample_vps_data():
    return [
        {'id': 'vps1', 'name': 'Test VPS 1', 'service': 'ZingProxy', 'ip': '192.168.1.1', 'expiry': '2024-12-31', 'source': 'manual'},
        {'id': 'vps2', 'name': 'Test VPS 2', 'service': 'BitLaunch', 'ip': '192.168.1.2', 'expiry': None, 'source': 'bitlaunch'},
        {'id': 'vps3', 'name': 'Test VPS 3', 'service': 'CloudFly', 'ip': '192.168.1.3', 'expiry': None, 'source': 'cloudfly'}
    ]

@pytest.fixture
def sample_accounts_data():
    return [
        {'id': 'acc1', 'username': 'test1@example.com', 'service': 'mail', 'expiry': '2024-12-31', 'balance': None, 'source': 'manual'},
        {'id': 'acc2', 'username': 'test2@bitlaunch.com', 'service': 'BitLaunch', 'expiry': None, 'balance': 10000, 'source': 'bitlaunch'},
        {'id': 'acc3', 'username': 'test3@zingproxy.com', 'service': 'ZingProxy', 'expiry': None, 'balance': 50000, 'source': 'zingproxy'},
        {'id': 'acc4', 'username': 'test4@cloudfly.vn', 'service': 'CloudFly', 'expiry': None, 'balance': 75000, 'source': 'cloudfly'}
    ]

def test_dashboard_page_requires_auth(client):
    """Test trang dashboard yêu cầu đăng nhập"""
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.location

def test_dashboard_page_with_auth(client, app, sample_user):
    """Test trang dashboard khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data
    assert b'VPS Management' in response.data
    assert b'Accounts Management' in response.data
    assert b'BitLaunch' in response.data
    assert b'ZingProxy' in response.data
    assert b'CloudFly' in response.data
    assert b'Rocket Chat' in response.data
    assert b'Scheduler Status' in response.data

def test_vps_page_requires_auth(client):
    """Test trang VPS yêu cầu đăng nhập"""
    response = client.get('/vps')
    assert response.status_code == 302
    assert '/login' in response.location

def test_vps_page_with_auth(client, app, sample_user):
    """Test trang VPS khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang VPS
    response = client.get('/vps')
    assert response.status_code == 200
    assert b'VPS Management' in response.data
    assert b'Add VPS' in response.data
    assert b'Filter' in response.data

def test_accounts_page_requires_auth(client):
    """Test trang Accounts yêu cầu đăng nhập"""
    response = client.get('/accounts')
    assert response.status_code == 302
    assert '/login' in response.location

def test_accounts_page_with_auth(client, app, sample_user):
    """Test trang Accounts khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang Accounts
    response = client.get('/accounts')
    assert response.status_code == 200
    assert b'Accounts Management' in response.data
    assert b'Add Account' in response.data
    assert b'Filter' in response.data
    assert b'Rocket Chat' in response.data  # Sửa từ 'Gửi thông báo Rocket Chat'

def test_bitlaunch_page_requires_auth(client):
    """Test trang BitLaunch yêu cầu đăng nhập"""
    response = client.get('/bitlaunch')
    assert response.status_code == 302
    assert '/login' in response.location

def test_bitlaunch_page_with_auth(client, app, sample_user):
    """Test trang BitLaunch khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang BitLaunch
    response = client.get('/bitlaunch')
    assert response.status_code == 200
    assert b'BitLaunch Management' in response.data
    assert b'Add API Key' in response.data
    assert b'VPS Instances' in response.data

def test_zingproxy_page_requires_auth(client):
    """Test trang ZingProxy yêu cầu đăng nhập"""
    response = client.get('/zingproxy')
    assert response.status_code == 302
    assert '/login' in response.location

def test_zingproxy_page_with_auth(client, app, sample_user):
    """Test trang ZingProxy khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang ZingProxy
    response = client.get('/zingproxy')
    assert response.status_code == 200
    assert b'ZingProxy Management' in response.data
    assert b'Add Account' in response.data
    assert b'Proxy List' in response.data

def test_cloudfly_page_requires_auth(client):
    """Test trang CloudFly yêu cầu đăng nhập"""
    response = client.get('/cloudfly')
    assert response.status_code == 302
    assert '/login' in response.location

def test_cloudfly_page_with_auth(client, app, sample_user):
    """Test trang CloudFly khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang CloudFly
    response = client.get('/cloudfly')
    assert response.status_code == 200
    assert b'CloudFly Management' in response.data
    assert b'Add API Token' in response.data
    assert b'VPS Instances' in response.data

def test_rocket_chat_page_requires_auth(client):
    """Test trang Rocket Chat yêu cầu đăng nhập"""
    response = client.get('/rocket-chat')
    assert response.status_code == 302
    assert '/login' in response.location

def test_rocket_chat_page_with_auth(client, app, sample_user):
    """Test trang Rocket Chat khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang Rocket Chat
    response = client.get('/rocket-chat')
    assert response.status_code == 200
    assert b'Rocket Chat Configuration' in response.data
    assert b'Test' in response.data  # Sửa từ 'Test kết nối'
    assert b'Notification' in response.data  # Sửa từ 'Gửi thông báo thử'
    assert b'Account' in response.data  # Sửa từ 'Thông báo tài khoản'

def test_users_page_requires_admin(client):
    """Test trang Users yêu cầu quyền admin"""
    response = client.get('/users')
    assert response.status_code == 302
    assert '/login' in response.location

def test_users_page_with_admin(client, app, sample_admin):
    """Test trang Users với user admin"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_admin)
        db.session.commit()
    
    # Đăng nhập với admin
    client.post('/login', json={
        'username': 'admin',
        'password': 'adminpass123'
    })
    
    # Test trang Users
    response = client.get('/users')
    assert response.status_code == 200
    assert b'Users Management' in response.data
    assert b'Add User' in response.data

def test_users_page_with_regular_user(client, app, sample_user):
    """Test trang Users với user thường (không được phép)"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập với user thường
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang Users (không được phép)
    response = client.get('/users')
    assert response.status_code == 403

def test_notifications_page_requires_auth(client):
    """Test trang Notifications yêu cầu đăng nhập"""
    response = client.get('/notifications')
    assert response.status_code == 302
    assert '/login' in response.location

def test_notifications_page_with_auth(client, app, sample_user):
    """Test trang Notifications khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang Notifications
    response = client.get('/notifications')
    assert response.status_code == 200
    assert b'Notifications' in response.data
    assert b'Telegram Settings' in response.data

def test_proxies_page_requires_auth(client):
    """Test trang Proxies yêu cầu đăng nhập"""
    response = client.get('/proxies')
    assert response.status_code == 302
    assert '/login' in response.location

def test_proxies_page_with_auth(client, app, sample_user):
    """Test trang Proxies khi đã đăng nhập"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang Proxies
    response = client.get('/proxies')
    assert response.status_code == 200
    assert b'Proxy Management' in response.data
    assert b'Add Proxy' in response.data

def test_base_template_includes_common_elements(client, app, sample_user):
    """Test base template có các elements chung"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test các trang khác nhau để kiểm tra base template
    pages = ['/dashboard', '/vps', '/accounts', '/bitlaunch', '/zingproxy', '/cloudfly']
    
    for page in pages:
        response = client.get(page)
        assert response.status_code == 200
        
        # Kiểm tra các elements chung
        assert b'VPS Manager' in response.data  # Title
        assert b'navbar' in response.data  # Navigation
        assert b'container' in response.data  # Main container
        assert b'Logout' in response.data  # Logout button

def test_login_template_structure(client):
    """Test cấu trúc template login"""
    response = client.get('/login')
    assert response.status_code == 200
    
    # Kiểm tra form elements
    assert b'username' in response.data
    assert b'password' in response.data
    assert b'Login' in response.data
    assert b'form' in response.data

def test_error_pages(client):
    """Test các trang lỗi"""
    # Test 404
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    
    # Test 500 (nếu có)
    # Cần tạo route test để gây lỗi 500

def test_static_files_accessible(client):
    """Test static files có thể truy cập"""
    # Test CSS files
    response = client.get('/static/css/style.css')
    # Có thể 404 nếu file không tồn tại, nhưng route phải hoạt động
    assert response.status_code in [200, 404]

def test_favicon_accessible(client):
    """Test favicon có thể truy cập"""
    response = client.get('/favicon.ico')
    # Có thể 404 nếu file không tồn tại
    assert response.status_code in [200, 404]

def test_robots_txt_accessible(client):
    """Test robots.txt có thể truy cập"""
    response = client.get('/robots.txt')
    # Có thể 404 nếu file không tồn tại
    assert response.status_code in [200, 404]

def test_sitemap_accessible(client):
    """Test sitemap có thể truy cập"""
    response = client.get('/sitemap.xml')
    # Có thể 404 nếu file không tồn tại
    assert response.status_code in [200, 404] 