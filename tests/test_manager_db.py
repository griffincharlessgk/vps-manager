import pytest
from ui.app import create_app
from core.models import db, VPS, Account

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as client:
        yield client

def test_crud_vps(client):
    # Thêm VPS
    vps = {
        'id': 'vps1',
        'service': 'TestService',
        'name': 'VPS 1',
        'ip': '1.2.3.4',
        'expiry': '2025-01-01'
    }
    res = client.post('/api/vps', json=vps)
    assert res.status_code == 201
    # Lấy danh sách VPS
    res = client.get('/api/vps')
    data = res.get_json()
    assert any(x['id'] == 'vps1' for x in data)
    # Sửa VPS
    update = {'service': 'Changed', 'name': 'VPS 1 edit', 'ip': '5.6.7.8', 'expiry': '2026-01-01'}
    res = client.put('/api/vps/vps1', json=update)
    assert res.status_code == 200
    res = client.get('/api/vps')
    data = res.get_json()
    assert any(x['service'] == 'Changed' for x in data)
    # Xóa VPS
    res = client.delete('/api/vps/vps1')
    assert res.status_code == 200
    res = client.get('/api/vps')
    data = res.get_json()
    assert not any(x['id'] == 'vps1' for x in data)

def test_crud_account(client):
    # Thêm Account
    acc = {
        'id': 'acc1',
        'service': 'TestService',
        'username': 'user1',
        'expiry': '2025-01-01'
    }
    res = client.post('/api/accounts', json=acc)
    assert res.status_code == 201
    # Lấy danh sách Account
    res = client.get('/api/accounts')
    data = res.get_json()
    assert any(x['id'] == 'acc1' for x in data)
    # Sửa Account
    update = {'service': 'Changed', 'username': 'user1edit', 'expiry': '2026-01-01'}
    res = client.put('/api/accounts/acc1', json=update)
    assert res.status_code == 200
    res = client.get('/api/accounts')
    data = res.get_json()
    assert any(x['service'] == 'Changed' for x in data)
    # Xóa Account
    res = client.delete('/api/accounts/acc1')
    assert res.status_code == 200
    res = client.get('/api/accounts')
    data = res.get_json()
    assert not any(x['id'] == 'acc1' for x in data) 