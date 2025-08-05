import pytest
from unittest.mock import patch, MagicMock
from core import manager
from core.scheduler import start_scheduler

@pytest.fixture(autouse=True)
def clear_data():
    manager.clear_vps()
    manager.clear_accounts()

@patch('core.notifier.notify_expiry_telegram')
def test_scheduler_registers_and_runs(mock_notify):
    # Thêm dữ liệu mẫu
    manager.add_vps({'id': 'vps1', 'service': 'ZingProxy', 'name': 'VPS 1', 'ip': '1.1.1.1', 'expiry': '2099-12-31'})
    manager.add_account({'id': 'acc1', 'service': 'mail', 'username': 'user', 'password': 'x', 'expiry': '2099-12-31'})
    scheduler = start_scheduler()
    # Lấy job
    job = scheduler.get_job('expiry_warnings')
    assert job is not None
    # Gọi job thủ công để test
    job.func()
    # Đảm bảo notify_expiry_telegram được gọi cho cả VPS và account
    assert mock_notify.call_count == 2
    scheduler.shutdown() 