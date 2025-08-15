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

def test_vps_page_javascript_includes(client, app, sample_user):
    """Test VPS page có JavaScript cần thiết"""
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
    
    # Kiểm tra JavaScript functions
    assert b'function addVps()' in response.data
    assert b'function editVps()' in response.data
    assert b'function deleteVps()' in response.data
    assert b'function filterVps()' in response.data
    assert b'function renderVpsTable()' in response.data

def test_accounts_page_javascript_includes(client, app, sample_user):
    """Test Accounts page có JavaScript cần thiết"""
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
    
    # Kiểm tra JavaScript functions
    assert b'function addAccount()' in response.data
    assert b'function editAccount()' in response.data
    assert b'function deleteAccount()' in response.data
    assert b'function filterAccounts()' in response.data
    assert b'function renderAccTable()' in response.data
    assert b'function sendRocketChatNotification()' in response.data

def test_bitlaunch_page_javascript_includes(client, app, sample_user):
    """Test BitLaunch page có JavaScript cần thiết"""
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
    
    # Kiểm tra JavaScript functions
    assert b'function addBitlaunchApi()' in response.data
    assert b'function editBitlaunchApi()' in response.data
    assert b'function deleteBitlaunchApi()' in response.data
    assert b'function loadApis()' in response.data
    assert b'function loadVps()' in response.data

def test_zingproxy_page_javascript_includes(client, app, sample_user):
    """Test ZingProxy page có JavaScript cần thiết"""
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
    
    # Kiểm tra JavaScript functions
    assert b'function addZingProxyAccount()' in response.data
    assert b'function editZingProxyAccount()' in response.data
    assert b'function deleteZingProxyAccount()' in response.data
    assert b'function loadAccounts()' in response.data
    assert b'function loadProxies()' in response.data

def test_cloudfly_page_javascript_includes(client, app, sample_user):
    """Test CloudFly page có JavaScript cần thiết"""
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
    
    # Kiểm tra JavaScript functions
    assert b'function addCloudflyApi()' in response.data
    assert b'function editCloudflyApi()' in response.data
    assert b'function deleteCloudflyApi()' in response.data
    assert b'function loadApis()' in response.data
    assert b'function loadVps()' in response.data

def test_rocket_chat_page_javascript_includes(client, app, sample_user):
    """Test Rocket Chat page có JavaScript cần thiết"""
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
    
    # Kiểm tra JavaScript functions
    assert b'function saveConfig()' in response.data
    assert b'function testConnection()' in response.data
    assert b'function sendTestNotification()' in response.data
    assert b'function loadConfig()' in response.data
    assert b'function sendDetailedInfo()' in response.data

def test_dashboard_page_javascript_includes(client, app, sample_user):
    """Test Dashboard page có JavaScript cần thiết"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test trang Dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200
    
    # Kiểm tra JavaScript functions
    assert b'function checkSchedulerStatus()' in response.data
    assert b'window.onload' in response.data

def test_users_page_javascript_includes(client, app, sample_user):
    """Test Users page có JavaScript cần thiết (admin only)"""
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

def test_proxies_page_javascript_includes(client, app, sample_user):
    """Test Proxies page có JavaScript cần thiết"""
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
    
    # Kiểm tra JavaScript functions
    assert b'function addProxy()' in response.data
    assert b'function editProxy()' in response.data
    assert b'function deleteProxy()' in response.data
    assert b'function filterProxies()' in response.data

def test_notifications_page_javascript_includes(client, app, sample_user):
    """Test Notifications page có JavaScript cần thiết"""
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
    
    # Kiểm tra JavaScript functions
    assert b'function saveTelegramSettings()' in response.data
    assert b'function testTelegramConnection()' in response.data

def test_base_template_javascript_includes(client, app, sample_user):
    """Test base template có JavaScript chung"""
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
        
        # Kiểm tra JavaScript chung
        assert b'</script>' in response.data  # Có JavaScript tags
        assert b'function' in response.data  # Có JavaScript functions

def test_modal_dialogs_exist(client, app, sample_user):
    """Test các modal dialogs tồn tại"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test VPS page có modal
    response = client.get('/vps')
    assert response.status_code == 200
    assert b'modal' in response.data
    assert b'Add VPS Modal' in response.data or b'addVpsModal' in response.data
    
    # Test Accounts page có modal
    response = client.get('/accounts')
    assert response.status_code == 200
    assert b'modal' in response.data
    assert b'Add Account Modal' in response.data or b'addAccountModal' in response.data

def test_form_validation_javascript(client, app, sample_user):
    """Test JavaScript form validation"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test VPS page có validation
    response = client.get('/vps')
    assert response.status_code == 200
    assert b'required' in response.data or b'validation' in response.data
    
    # Test Accounts page có validation
    response = client.get('/accounts')
    assert response.status_code == 200
    assert b'required' in response.data or b'validation' in response.data

def test_api_calls_javascript(client, app, sample_user):
    """Test JavaScript API calls"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test VPS page có API calls
    response = client.get('/vps')
    assert response.status_code == 200
    assert b'fetch(' in response.data or b'$.ajax(' in response.data or b'axios.' in response.data
    
    # Test Accounts page có API calls
    response = client.get('/accounts')
    assert response.status_code == 200
    assert b'fetch(' in response.data or b'$.ajax(' in response.data or b'axios.' in response.data

def test_error_handling_javascript(client, app, sample_user):
    """Test JavaScript error handling"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test VPS page có error handling
    response = client.get('/vps')
    assert response.status_code == 200
    assert b'catch(' in response.data or b'error' in response.data
    
    # Test Accounts page có error handling
    response = client.get('/accounts')
    assert response.status_code == 200
    assert b'catch(' in response.data or b'error' in response.data

def test_ui_interactions_javascript(client, app, sample_user):
    """Test JavaScript UI interactions"""
    with app.app_context():
        from core.models import db
        db.session.add(sample_user)
        db.session.commit()
    
    # Đăng nhập
    client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Test VPS page có UI interactions
    response = client.get('/vps')
    assert response.status_code == 200
    assert b'onclick=' in response.data or b'addEventListener(' in response.data
    
    # Test Accounts page có UI interactions
    response = client.get('/accounts')
    assert response.status_code == 200
    assert b'onclick=' in response.data or b'addEventListener(' in response.data 