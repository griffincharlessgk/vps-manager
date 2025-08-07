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
            logger.info(f"[Scheduler] Found {len(accs)} ZingProxy accounts needing update")
            
            updated_count = 0
            total_proxies_imported = 0
            
            for acc in accs:
                try:
                    logger.info(f"[Scheduler] Updating ZingProxy account {acc.id} ({acc.email})")
                    client = ZingProxyClient(access_token=acc.access_token)
                    
                    # Cập nhật thông tin tài khoản
                    user_info = client.get_account_details()
                    balance = user_info.get('balance', 0)
                    manager.update_zingproxy_account(acc.id, balance)
                    logger.info(f"[Scheduler] Updated balance for account {acc.id}: ${balance}")
                    
                    # Cập nhật danh sách proxy trong ZingProxy
                    proxies = client.get_all_active_proxies()
                    manager.update_zingproxy_list(acc.id, proxies)
                    logger.info(f"[Scheduler] Updated {len(proxies)} proxies for account {acc.id}")
                    
                    # Tự động import proxy vào hệ thống quản lý proxy
                    try:
                        zingproxy_data = []
                        for proxy in proxies:
                            zingproxy_data.append({
                                'proxy_id': proxy.get('proxy_id'),
                                'ip': proxy.get('ip'),
                                'port': proxy.get('port'),
                                'port_socks5': proxy.get('port_socks5'),
                                'username': proxy.get('username'),
                                'password': proxy.get('password'),
                                'status': proxy.get('status'),
                                'expire_at': proxy.get('expire_at'),
                                'location': proxy.get('location'),
                                'type': proxy.get('type'),
                                'note': proxy.get('note'),
                                'auto_renew': proxy.get('auto_renew')
                            })
                        
                        if zingproxy_data:
                            imported_count = manager.import_proxies_from_zingproxy(acc.user_id, zingproxy_data)
                            total_proxies_imported += imported_count
                            logger.info(f"[Scheduler] Imported {imported_count} proxies to proxy management system for account {acc.id}")
                    except Exception as e:
                        logger.error(f"[Scheduler] Error importing proxies to management system for account {acc.id}: {e}")
                    
                    updated_count += 1
                except ZingProxyAPIError as e:
                    logger.error(f"[Scheduler] ZingProxy API error for account {acc.id}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"[Scheduler] Error updating ZingProxy account {acc.id}: {e}")
                    continue
            
            logger.info(f"[Scheduler] Successfully updated {updated_count}/{len(accs)} ZingProxy accounts")
            logger.info(f"[Scheduler] Total proxies imported to management system: {total_proxies_imported}")

    def auto_sync_zingproxy_proxies():
        """Tự động đồng bộ proxy từ ZingProxy"""
        logger.info("[Scheduler] Running auto_sync_zingproxy_proxies job")
        with app.app_context():
            from core.api_clients.zingproxy import ZingProxyClient, ZingProxyAPIError
            from core.models import ZingProxyAccount
            
            # Lấy tất cả tài khoản ZingProxy
            accounts = ZingProxyAccount.query.all()
            logger.info(f"[Scheduler] Found {len(accounts)} ZingProxy accounts for auto sync")
            
            total_synced = 0
            failed_accounts = 0
            
            for acc in accounts:
                try:
                    logger.info(f"[Scheduler] Auto syncing proxies for account {acc.id} ({acc.email})")
                    client = ZingProxyClient(access_token=acc.access_token)
                    proxies = client.get_all_active_proxies()
                    
                    if proxies:
                        # Import vào hệ thống quản lý proxy
                        zingproxy_data = []
                        for proxy in proxies:
                            zingproxy_data.append({
                                'proxy_id': proxy.get('proxy_id'),
                                'ip': proxy.get('ip'),
                                'port': proxy.get('port'),
                                'port_socks5': proxy.get('port_socks5'),
                                'username': proxy.get('username'),
                                'password': proxy.get('password'),
                                'status': proxy.get('status'),
                                'expire_at': proxy.get('expire_at'),
                                'location': proxy.get('location'),
                                'type': proxy.get('type'),
                                'note': proxy.get('note'),
                                'auto_renew': proxy.get('auto_renew')
                            })
                        
                        imported_count = manager.import_proxies_from_zingproxy(acc.user_id, zingproxy_data)
                        total_synced += imported_count
                        logger.info(f"[Scheduler] Auto synced {imported_count} proxies for account {acc.id}")
                    else:
                        logger.info(f"[Scheduler] No proxies found for account {acc.id}")
                        
                except Exception as e:
                    logger.error(f"[Scheduler] Error auto syncing proxies for account {acc.id}: {e}")
                    failed_accounts += 1
                    continue
            
            logger.info(f"[Scheduler] Auto sync completed: {total_synced} proxies synced, {failed_accounts} accounts failed")

    def update_cloudfly_apis():
        """Tự động cập nhật thông tin tài khoản CloudFly theo tần suất"""
        logger.info("[Scheduler] Running update_cloudfly_apis job")
        with app.app_context():
            from core.api_clients.cloudfly import CloudFlyClient, CloudFlyAPIError
            apis = manager.get_cloudfly_apis_needing_update()
            logger.info(f"[Scheduler] Found {len(apis)} CloudFly APIs needing update")
            
            updated_count = 0
            for api in apis:
                try:
                    logger.info(f"[Scheduler] Updating CloudFly API {api.id} ({api.email})")
                    client = CloudFlyClient(api.api_token)
                    
                    # Cập nhật thông tin tài khoản
                    user_info = client.get_user_info()
                    balance = user_info.get('balance', 0)
                    account_limit = user_info.get('account_limit', 0)
                    manager.update_cloudfly_info(api.id, balance, account_limit)
                    logger.info(f"[Scheduler] Updated balance for API {api.id}: ${balance}")
                    
                    updated_count += 1
                except CloudFlyAPIError as e:
                    logger.error(f"[Scheduler] CloudFly API error for API {api.id}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"[Scheduler] Error updating CloudFly API {api.id}: {e}")
                    continue
            
            logger.info(f"[Scheduler] Successfully updated {updated_count}/{len(apis)} CloudFly APIs")

    def update_cloudfly_vps():
        """Tự động cập nhật danh sách VPS CloudFly"""
        logger.info("[Scheduler] Running update_cloudfly_vps job")
        with app.app_context():
            from core.api_clients.cloudfly import CloudFlyClient, CloudFlyAPIError
            from core.models import CloudFlyAPI
            
            # Lấy tất cả tài khoản CloudFly
            apis = CloudFlyAPI.query.filter_by(is_active=True).all()
            logger.info(f"[Scheduler] Found {len(apis)} CloudFly APIs for VPS update")
            
            total_updated = 0
            failed_apis = 0
            
            for api in apis:
                try:
                    logger.info(f"[Scheduler] Updating VPS for CloudFly API {api.id} ({api.email})")
                    client = CloudFlyClient(api.api_token)
                    instances = client.list_instances()
                    
                    if instances:
                        manager.update_cloudfly_vps_list(api.id, instances)
                        total_updated += len(instances)
                        logger.info(f"[Scheduler] Updated {len(instances)} VPS instances for API {api.id}")
                    else:
                        logger.info(f"[Scheduler] No VPS instances found for API {api.id}")
                        
                except CloudFlyAPIError as e:
                    logger.error(f"[Scheduler] CloudFly API error for API {api.id}: {e}")
                    failed_apis += 1
                    continue
                except Exception as e:
                    logger.error(f"[Scheduler] Error updating CloudFly VPS for API {api.id}: {e}")
                    failed_apis += 1
                    continue
            
            logger.info(f"[Scheduler] CloudFly VPS update completed: {total_updated} instances updated, {failed_apis} APIs failed")

    # Lên lịch đồng bộ proxy từ ZingProxy hàng ngày lúc 2:00 sáng
    scheduler.add_job(
        auto_sync_zingproxy_proxies,
        'cron',
        hour=2,
        minute=0,
        id='auto_sync_zingproxy_proxies',
        replace_existing=True
    )
    
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
    
    # Lên lịch cập nhật ZingProxy mỗi 6 giờ để đảm bảo dữ liệu luôn mới
    scheduler.add_job(update_zingproxy_accounts, 'interval', hours=6, id='zingproxy_update_interval')
    
    # Lên lịch đồng bộ proxy từ ZingProxy mỗi 2 giờ
    scheduler.add_job(auto_sync_zingproxy_proxies, 'interval', hours=2, id='zingproxy_proxy_sync')
    
    # Lên lịch đồng bộ proxy từ ZingProxy mỗi ngày lúc 8h sáng
    scheduler.add_job(auto_sync_zingproxy_proxies, 'cron', hour=8, minute=0, id='zingproxy_proxy_sync_daily')
    
    # Lên lịch cập nhật CloudFly mỗi ngày lúc 8h sáng
    scheduler.add_job(update_cloudfly_apis, 'cron', hour=8, minute=0, id='cloudfly_update')
    scheduler.add_job(update_cloudfly_vps, 'cron', hour=8, minute=30, id='cloudfly_vps_update')
    
    # Lên lịch cập nhật CloudFly mỗi 6 giờ để đảm bảo dữ liệu luôn mới
    scheduler.add_job(update_cloudfly_apis, 'interval', hours=6, id='cloudfly_update_interval')
    scheduler.add_job(update_cloudfly_vps, 'interval', hours=6, id='cloudfly_vps_update_interval')
    
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