import pytest
from datetime import datetime, timedelta
from core import notifier

class DummySender:
    def __init__(self):
        self.messages = []
    def send(self, msg: str) -> None:
        self.messages.append(msg)

@pytest.fixture
def soon_expired_vps():
    return [
        {'id': 'vps1', 'name': 'VPS 1', 'expiry': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')},
        {'id': 'vps2', 'name': 'VPS 2', 'expiry': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')},
    ]

@pytest.fixture
def soon_expired_accounts():
    return [
        {'id': 'acc1', 'service': 'mail', 'username': 'user1', 'expiry': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')},
        {'id': 'acc2', 'service': 'proxy', 'username': 'user2', 'expiry': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')},
    ]

def test_notify_vps_expiry(soon_expired_vps):
    sender = DummySender()
    notifier.notify_expiry(soon_expired_vps, sender.send, days_before=3, item_type='VPS')
    assert any('VPS 1' in msg for msg in sender.messages)
    assert not any('VPS 2' in msg for msg in sender.messages)

def test_notify_account_expiry(soon_expired_accounts):
    sender = DummySender()
    notifier.notify_expiry(soon_expired_accounts, sender.send, days_before=3, item_type='Account')
    assert any('user1' in msg for msg in sender.messages)
    assert not any('user2' in msg for msg in sender.messages) 