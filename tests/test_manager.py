import pytest
from core import manager

@pytest.fixture
def sample_vps():
    return {
        'id': 'vps1',
        'service': 'ZingProxy',
        'name': 'VPS 1',
        'ip': '192.168.1.1',
        'expiry': '2024-12-31'
    }

@pytest.fixture
def sample_account():
    return {
        'id': 'acc1',
        'service': 'mail',
        'username': 'user@example.com',
        'password': 'secret',
        'expiry': '2024-12-31'
    }

def test_add_vps(sample_vps):
    manager.clear_vps()
    manager.add_vps(sample_vps)
    vps_list = manager.list_vps()
    assert any(v['id'] == sample_vps['id'] and v['service'] == sample_vps['service'] for v in vps_list)

def test_update_vps(sample_vps):
    manager.clear_vps()
    manager.add_vps(sample_vps)
    updated = sample_vps.copy()
    updated['name'] = 'VPS 1 Updated'
    updated['service'] = 'ProxyVIP'
    manager.update_vps(updated['id'], updated)
    vps = manager.get_vps(updated['id'])
    assert vps['name'] == 'VPS 1 Updated'
    assert vps['service'] == 'ProxyVIP'

def test_delete_vps(sample_vps):
    manager.clear_vps()
    manager.add_vps(sample_vps)
    manager.delete_vps(sample_vps['id'])
    vps = manager.get_vps(sample_vps['id'])
    assert vps is None

def test_vps_expiry(sample_vps):
    manager.clear_vps()
    manager.add_vps(sample_vps)
    exp = manager.get_vps_expiry(sample_vps['id'])
    assert exp == '2024-12-31'

def test_add_account(sample_account):
    manager.clear_accounts()
    manager.add_account(sample_account)
    acc_list = manager.list_accounts()
    assert any(a['id'] == sample_account['id'] and a['service'] == sample_account['service'] for a in acc_list)

def test_update_account(sample_account):
    manager.clear_accounts()
    manager.add_account(sample_account)
    updated = sample_account.copy()
    updated['password'] = 'newpass'
    updated['service'] = 'proxy'
    manager.update_account(updated['id'], updated)
    acc = manager.get_account(updated['id'])
    assert acc['password'] == 'newpass'
    assert acc['service'] == 'proxy'

def test_delete_account(sample_account):
    manager.clear_accounts()
    manager.add_account(sample_account)
    manager.delete_account(sample_account['id'])
    acc = manager.get_account(sample_account['id'])
    assert acc is None

def test_account_expiry(sample_account):
    manager.clear_accounts()
    manager.add_account(sample_account)
    exp = manager.get_account_expiry(sample_account['id'])
    assert exp == '2024-12-31' 