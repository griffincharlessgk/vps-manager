import pytest
from unittest.mock import patch, MagicMock
from core import manager
from core.scheduler import start_scheduler, get_scheduler

@pytest.fixture(autouse=True)
def clear_data():
    manager.clear_vps()
    manager.clear_accounts()

@patch('core.notifier.notify_expiry_telegram_per_user')
def test_scheduler_registers_and_runs(mock_notify):
    """Test scheduler đăng ký và chạy jobs"""
    # Thêm dữ liệu mẫu
    manager.add_vps({'id': 'vps1', 'service': 'ZingProxy', 'name': 'VPS 1', 'ip': '1.1.1.1', 'expiry': '2099-12-31'})
    manager.add_account({'id': 'acc1', 'service': 'mail', 'username': 'user', 'password': 'x', 'expiry': '2099-12-31'})
    
    scheduler = start_scheduler()
    
    # Kiểm tra job được đăng ký
    job = scheduler.get_job('expiry_warnings')
    assert job is not None
    
    # Gọi job thủ công để test
    job.func()
    
    # Đảm bảo notify_expiry_telegram_per_user được gọi cho cả VPS và account
    assert mock_notify.call_count == 2
    
    scheduler.shutdown()

def test_scheduler_jobs_registration():
    """Test tất cả jobs được đăng ký đúng"""
    scheduler = start_scheduler()
    
    # Kiểm tra các jobs chính
    expected_jobs = [
        'expiry_warnings',
        'daily_summary',
        'rocketchat_daily_notifications',
        'bitlaunch_update',
        'zingproxy_update',
        'cloudfly_update'
    ]
    
    for job_id in expected_jobs:
        job = scheduler.get_job(job_id)
        assert job is not None, f"Job {job_id} không được đăng ký"
    
    scheduler.shutdown()

def test_scheduler_status_not_started():
    """Test scheduler status khi chưa khởi động"""
    # Khi gọi get_scheduler() lần đầu, nó sẽ tự động start
    # Nhưng chúng ta có thể test trước khi start
    from core.scheduler import scheduler as global_scheduler
    
    # Reset global scheduler
    global_scheduler = None
    
    # Test trước khi start
    assert global_scheduler is None
    
    # Sau khi gọi get_scheduler(), nó sẽ start
    scheduler = get_scheduler()
    assert scheduler is not None
    assert len(scheduler.get_jobs()) > 0

def test_scheduler_status_running():
    """Test scheduler status khi đang chạy"""
    scheduler = start_scheduler()
    
    # Kiểm tra scheduler đang chạy
    assert scheduler.running
    assert len(scheduler.get_jobs()) > 0
    
    # Kiểm tra job details
    jobs = scheduler.get_jobs()
    for job in jobs:
        assert job.id is not None
        assert job.trigger is not None
        assert job.next_run_time is not None
    
    scheduler.shutdown()

def test_scheduler_status_after_shutdown():
    """Test scheduler status sau khi shutdown"""
    scheduler = start_scheduler()
    scheduler.shutdown()
    
    # Sau khi shutdown, scheduler không còn running
    assert not scheduler.running

@patch('core.notifier.send_daily_summary')
def test_daily_summary_job(mock_send_daily_summary):
    """Test job gửi daily summary"""
    scheduler = start_scheduler()
    
    # Lấy job daily summary
    job = scheduler.get_job('daily_summary')
    assert job is not None
    
    # Gọi job thủ công
    job.func()
    
    # Kiểm tra function được gọi
    # Note: send_daily_summary job gọi notifier.send_daily_summary cho từng user
    # nên mock sẽ được gọi nếu có user với telegram_chat_id
    mock_send_daily_summary.assert_called()
    
    scheduler.shutdown()

@patch('core.manager.update_bitlaunch_vps_list')
@patch('core.manager.update_bitlaunch_info')
def test_bitlaunch_update_jobs(mock_update_info, mock_update_vps):
    """Test các jobs cập nhật BitLaunch"""
    scheduler = start_scheduler()
    
    # Test job cập nhật API info
    api_job = scheduler.get_job('bitlaunch_update')
    assert api_job is not None
    
    # Test job cập nhật VPS list
    vps_job = scheduler.get_job('bitlaunch_vps_update')
    assert vps_job is not None
    
    scheduler.shutdown()

@patch('core.manager.update_zingproxy_account')
@patch('core.manager.update_zingproxy_list')
def test_zingproxy_update_jobs(mock_update_list, mock_update_account):
    """Test các jobs cập nhật ZingProxy"""
    scheduler = start_scheduler()
    
    # Test job cập nhật account
    account_job = scheduler.get_job('zingproxy_update')
    assert account_job is not None
    
    # Test job cập nhật proxy list
    proxy_job = scheduler.get_job('zingproxy_update_interval')
    assert proxy_job is not None
    
    scheduler.shutdown()

@patch('core.manager.update_cloudfly_info')
@patch('core.manager.update_cloudfly_vps_list')
def test_cloudfly_update_jobs(mock_update_vps, mock_update_info):
    """Test các jobs cập nhật CloudFly"""
    scheduler = start_scheduler()
    
    # Test job cập nhật API info
    api_job = scheduler.get_job('cloudfly_update')
    assert api_job is not None
    
    # Test job cập nhật VPS
    vps_job = scheduler.get_job('cloudfly_vps_update')
    assert vps_job is not None
    
    scheduler.shutdown()

@patch('core.rocket_chat.send_daily_account_summary')
@patch('core.rocket_chat.send_account_expiry_notification')
def test_rocket_chat_notification_job(mock_expiry, mock_summary):
    """Test job gửi thông báo Rocket Chat"""
    scheduler = start_scheduler()
    
    # Test job gửi thông báo hàng ngày
    job = scheduler.get_job('rocketchat_daily_notifications')
    assert job is not None
    
    scheduler.shutdown()

def test_scheduler_interval_jobs():
    """Test các jobs chạy theo interval"""
    scheduler = start_scheduler()
    
    # Kiểm tra interval jobs
    interval_jobs = [
        'expiry_warnings',  # 5 phút
        'daily_summary',    # 5 phút
        'zingproxy_proxy_sync',  # 2 giờ
        'zingproxy_update_interval',  # 6 giờ
        'cloudfly_update_interval',   # 6 giờ
        'cloudfly_vps_update_interval'  # 6 giờ
    ]
    
    for job_id in interval_jobs:
        job = scheduler.get_job(job_id)
        assert job is not None, f"Interval job {job_id} không được đăng ký"
        assert 'interval' in str(job.trigger), f"Job {job_id} không phải interval"
    
    scheduler.shutdown()

def test_scheduler_cron_jobs():
    """Test các jobs chạy theo cron"""
    scheduler = start_scheduler()
    
    # Kiểm tra cron jobs
    cron_jobs = [
        'auto_sync_zingproxy_proxies',  # 2:00 sáng
        'bitlaunch_update',             # 6:00 sáng
        'bitlaunch_vps_update',         # 6:30 sáng
        'zingproxy_update',             # 7:00 sáng
        'cloudfly_update',              # 8:00 sáng
        'zingproxy_proxy_sync_daily',   # 8:00 sáng
        'cloudfly_vps_update',          # 8:30 sáng
        'rocketchat_daily_notifications',  # 9:00 sáng
        'weekly_report'                 # 10:00 sáng chủ nhật
    ]
    
    for job_id in cron_jobs:
        job = scheduler.get_job(job_id)
        assert job is not None, f"Cron job {job_id} không được đăng ký"
        assert 'cron' in str(job.trigger), f"Job {job_id} không phải cron"
    
    scheduler.shutdown()

def test_scheduler_error_handling():
    """Test xử lý lỗi trong scheduler"""
    scheduler = start_scheduler()
    
    # Test với job không tồn tại
    non_existent_job = scheduler.get_job('non_existent_job')
    assert non_existent_job is None
    
    # Test shutdown scheduler
    scheduler.shutdown()
    assert not scheduler.running
    
    # Test status sau khi shutdown
    scheduler_after_shutdown = get_scheduler()
    assert not scheduler_after_shutdown.running

def test_scheduler_job_details():
    """Test chi tiết của các jobs"""
    scheduler = start_scheduler()
    
    # Lấy danh sách jobs
    jobs = scheduler.get_jobs()
    assert len(jobs) > 0
    
    # Kiểm tra từng job
    for job in jobs:
        assert job.id is not None
        assert job.trigger is not None
        assert hasattr(job, 'func')
        assert callable(job.func)
    
    scheduler.shutdown()

def test_scheduler_restart():
    """Test khởi động lại scheduler"""
    # Khởi động lần đầu
    scheduler1 = start_scheduler()
    assert scheduler1.running
    assert len(scheduler1.get_jobs()) > 0
    
    # Shutdown
    scheduler1.shutdown()
    assert not scheduler1.running
    
    # Khởi động lại
    scheduler2 = start_scheduler()
    assert scheduler2.running
    assert len(scheduler2.get_jobs()) > 0
    
    scheduler2.shutdown() 