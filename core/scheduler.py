from apscheduler.schedulers.background import BackgroundScheduler
from core import manager, notifier
from core.models import User
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    from ui.app import create_app
    app = create_app()
    
    scheduler = BackgroundScheduler()
    
    def send_expiry_warnings():
        """Gửi cảnh báo hết hạn theo giờ của từng user"""
        logger.info("[Scheduler] Running send_expiry_warnings job")
        with app.app_context():
            # Kiểm tra TELEGRAM_TOKEN
            token = os.getenv('TELEGRAM_TOKEN')
            if not token:
                logger.warning("[Scheduler] TELEGRAM_TOKEN not found")
                return
            
            # Kiểm tra users có Chat ID
            users = User.query.filter(User.telegram_chat_id.isnot(None)).all()
            if not users:
                logger.warning("[Scheduler] No users with telegram_chat_id found")
                return
            
            logger.info(f"[Scheduler] Found {len(users)} users with telegram_chat_id")
            
            # Lấy dữ liệu
            try:
                vps_list = manager.list_vps()
                acc_list = manager.list_accounts()
                logger.info(f"[Scheduler] Found {len(vps_list)} VPS and {len(acc_list)} accounts")
                notifier.notify_expiry_telegram_per_user(vps_list, item_type='VPS')
                notifier.notify_expiry_telegram_per_user(acc_list, item_type='Account')
            except Exception as e:
                logger.error(f"[Scheduler] Error in send_expiry_warnings: {e}")
    
    def send_daily_summary():
        """Gửi báo cáo tổng hợp theo giờ của từng user"""
        logger.info("[Scheduler] Running send_daily_summary job")
        with app.app_context():
            users = User.query.all()
            logger.info(f"[Scheduler] Found {len(users)} total users")
            for user in users:
                if not user.telegram_chat_id:
                    continue
                try:
                    logger.info(f"[Scheduler] Sending daily summary to user {user.username}")
                    notifier.send_daily_summary(user)
                except Exception as e:
                    logger.error(f"[Scheduler] Error sending daily summary to {user.username}: {e}")
    
    def send_weekly_report():
        """Gửi báo cáo tuần cho admin"""
        logger.info("[Scheduler] Running send_weekly_report job")
        with app.app_context():
            # TODO: Implement weekly report
            pass
    
    def update_bitlaunch_apis():
        """Tự động cập nhật thông tin tài khoản BitLaunch theo tần suất"""
        logger.info("[Scheduler] Running update_bitlaunch_apis job")
        with app.app_context():
            apis = manager.get_bitlaunch_apis_needing_update()
            for api in apis:
                try:
                    from core.api_clients.bitlaunch import BitLaunchClient
                    client = BitLaunchClient(api.api_key)
                    account_info = client.get_account_info()
                    manager.update_bitlaunch_api_info(api.id, account_info)
                except Exception as e:
                    logger.error(f"[Scheduler] Error updating BitLaunch API {api.id}: {e}")
    
    def update_bitlaunch_vps():
        """Tự động cập nhật danh sách VPS BitLaunch"""
        logger.info("[Scheduler] Running update_bitlaunch_vps job")
        with app.app_context():
            apis = manager.list_bitlaunch_apis()
            for api in apis:
                try:
                    from core.api_clients.bitlaunch import BitLaunchClient
                    client = BitLaunchClient(api.api_key)
                    servers = client.get_servers()
                    manager.update_bitlaunch_vps_list(api.id, servers)
                except Exception as e:
                    logger.error(f"[Scheduler] Error updating BitLaunch VPS for API {api.id}: {e}")
    
    def update_zingproxy_accounts():
        """Tự động cập nhật thông tin tài khoản và proxy ZingProxy theo tần suất"""
        logger.info("[Scheduler] Running update_zingproxy_accounts job")
        with app.app_context():
            from core.api_clients.zingproxy import ZingProxyClient, ZingProxyAPIError
            accs = manager.get_zingproxy_accounts_needing_update()
            for acc in accs:
                try:
                    client = ZingProxyClient(acc.email, '', access_token=acc.access_token)
                    user_info = client.get_account_details()
                    balance = user_info.get('balance', 0)
                    manager.update_zingproxy_account(acc.id, balance)
                    proxies = client.get_all_active_proxies()
                    manager.update_zingproxy_list(acc.id, proxies)
                except ZingProxyAPIError:
                    continue

    # Lên lịch gửi cảnh báo hết hạn mỗi 5 phút để kiểm tra notify_hour của từng user
    scheduler.add_job(send_expiry_warnings, 'interval', minutes=5, id='expiry_warnings')
    
    # Lên lịch gửi báo cáo tổng hợp mỗi 5 phút để kiểm tra notify_hour của từng user
    scheduler.add_job(send_daily_summary, 'interval', minutes=5, id='daily_summary')
    
    # Lên lịch gửi báo cáo tuần vào chủ nhật lúc 10h sáng
    scheduler.add_job(send_weekly_report, 'cron', day_of_week='sun', hour=10, minute=0, id='weekly_report')
    
    # Lên lịch cập nhật BitLaunch mỗi ngày lúc 6h sáng
    scheduler.add_job(update_bitlaunch_apis, 'cron', hour=6, minute=0, id='bitlaunch_update')
    scheduler.add_job(update_bitlaunch_vps, 'cron', hour=6, minute=30, id='bitlaunch_vps_update')
    
    # Lên lịch cập nhật ZingProxy mỗi ngày lúc 7h sáng
    scheduler.add_job(update_zingproxy_accounts, 'cron', hour=7, minute=0, id='zingproxy_update')
    
    logger.info(f"[Scheduler] Starting scheduler with {len(scheduler.get_jobs())} jobs")
    scheduler.start()
    return scheduler

# Global scheduler instance
scheduler = None

def get_scheduler():
    """Lấy scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = start_scheduler()
    return scheduler 