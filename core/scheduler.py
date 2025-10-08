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
        """Gửi cảnh báo hết hạn qua RocketChat cho users có cấu hình"""
        logger.info("[Scheduler] Running send_expiry_warnings job")
        with app.app_context():
            from core.models import RocketChatConfig
            
            # Kiểm tra users có cấu hình RocketChat
            configs = RocketChatConfig.query.filter_by(is_active=True).all()
            if not configs:
                logger.info("[Scheduler] No active RocketChat configurations found")
                return
            
            logger.info(f"[Scheduler] Found {len(configs)} active RocketChat configurations")
            
            # Lấy dữ liệu
            try:
                vps_list = manager.list_vps()
                acc_list = manager.list_accounts()
                logger.info(f"[Scheduler] Found {len(vps_list)} VPS and {len(acc_list)} accounts")
                
                # Gửi thông báo qua RocketChat cho từng user
                for config in configs:
                    user = User.query.get(config.user_id)
                    if not user:
                        continue
                    
                    # Gửi thông báo VPS
                    notifier.notify_expiry_rocketchat_per_user(vps_list, item_type='VPS', user=user, config=config)
                    # Gửi thông báo Account
                    notifier.notify_expiry_rocketchat_per_user(acc_list, item_type='Account', user=user, config=config)
                    
            except Exception as e:
                logger.error(f"[Scheduler] Error in send_expiry_warnings: {e}")
    
    def send_daily_summary():
        """Gửi báo cáo tổng hợp qua RocketChat cho users có cấu hình"""
        logger.info("[Scheduler] Running send_daily_summary job")
        with app.app_context():
            from core.models import RocketChatConfig
            
            configs = RocketChatConfig.query.filter_by(is_active=True).all()
            logger.info(f"[Scheduler] Found {len(configs)} active RocketChat configurations")
            
            for config in configs:
                user = User.query.get(config.user_id)
                if not user:
                    continue
                try:
                    logger.info(f"[Scheduler] Sending daily summary to user {user.username}")
                    notifier.send_daily_summary_rocketchat(user, config)
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
            from core.api_clients.bitlaunch import BitLaunchClient, BitLaunchAPIError
            
            apis = manager.get_bitlaunch_apis_needing_update()
            logger.info(f"[Scheduler] Found {len(apis)} BitLaunch APIs needing update")
            
            updated_count = 0
            for api in apis:
                try:
                    logger.info(f"[Scheduler] Updating BitLaunch API {api.id} ({api.email})")
                    client = BitLaunchClient(api.api_key)
                    account_info = client.get_account_info()
                    
                    # BitLaunch API trả về balance và limit theo đơn vị milli-dollars (1/1000)
                    balance = account_info.get('balance', 0) / 1000
                    limit = account_info.get('limit', 0) / 1000
                    
                    manager.update_bitlaunch_info(api.id, balance, limit)
                    logger.info(f"[Scheduler] Updated BitLaunch API {api.id}: balance=${balance:.3f}, limit=${limit:.3f}")
                    updated_count += 1
                except BitLaunchAPIError as e:
                    logger.error(f"[Scheduler] BitLaunch API error for API {api.id}: {e}")
                except Exception as e:
                    logger.error(f"[Scheduler] Error updating BitLaunch API {api.id}: {e}")
            
            logger.info(f"[Scheduler] Successfully updated {updated_count}/{len(apis)} BitLaunch APIs")
    
    def update_bitlaunch_vps():
        """Tự động cập nhật danh sách VPS BitLaunch"""
        logger.info("[Scheduler] Running update_bitlaunch_vps job")
        with app.app_context():
            from core.api_clients.bitlaunch import BitLaunchClient, BitLaunchAPIError
            from core.models import BitLaunchAPI
            
            # Lấy tất cả BitLaunch APIs từ tất cả users
            apis = BitLaunchAPI.query.filter_by(is_active=True).all()
            logger.info(f"[Scheduler] Found {len(apis)} BitLaunch APIs for VPS update")
            
            total_updated = 0
            failed_apis = 0
            
            for api in apis:
                try:
                    logger.info(f"[Scheduler] Updating VPS for BitLaunch API {api.id} ({api.email})")
                    client = BitLaunchClient(api.api_key)
                    servers = client.list_servers()
                    
                    if servers:
                        manager.update_bitlaunch_vps_list(api.id, servers)
                        total_updated += len(servers)
                        logger.info(f"[Scheduler] Updated {len(servers)} VPS instances for API {api.id}")
                    else:
                        logger.info(f"[Scheduler] No VPS instances found for API {api.id}")
                        
                except BitLaunchAPIError as e:
                    logger.error(f"[Scheduler] BitLaunch API error for API {api.id}: {e}")
                    failed_apis += 1
                    continue
                except Exception as e:
                    logger.error(f"[Scheduler] Error updating BitLaunch VPS for API {api.id}: {e}")
                    failed_apis += 1
                    continue
            
            logger.info(f"[Scheduler] BitLaunch VPS update completed: {total_updated} instances updated, {failed_apis} APIs failed")
    
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
                    
                    # CloudFly API có structure phức tạp: clients[0].wallet.main_balance
                    main_balance = 0
                    if 'clients' in user_info and len(user_info['clients']) > 0:
                        wallet = user_info['clients'][0].get('wallet', {})
                        main_balance = wallet.get('main_balance', 0)
                    
                    # CloudFly API không có account_limit
                    manager.update_cloudfly_info(api.id, main_balance, 0)
                    logger.info(f"[Scheduler] Updated balance for API {api.id}: ${main_balance}")
                    
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

    def check_account_alerts_5min():
        """Kiểm tra và gửi cảnh báo tài khoản sắp hết hạn và balance thấp"""
        with app.app_context():
            try:
                from core.models import RocketChatConfig, User
                from core.rocket_chat import send_account_expiry_notification
                from core import manager
                
                logger.info("=" * 70)
                logger.info("[Scheduler] 🔔 Checking account alerts (12-hour interval)")
                logger.info("=" * 70)
                
                # Lấy tất cả cấu hình Rocket Chat
                configs = RocketChatConfig.query.filter_by(is_active=True).all()
                
                if not configs:
                    logger.info("[Scheduler] ⚠️ No Rocket Chat configurations found")
                    return
                
                logger.info(f"[Scheduler] Found {len(configs)} Rocket Chat configurations")
                
                for config in configs:
                    try:
                        user = User.query.get(config.user_id)
                        if not user:
                            logger.warning(f"[Scheduler] User {config.user_id} not found")
                            continue
                    
                        logger.info(f"[Scheduler] 👤 Processing user: {user.username}")
                    
                        # Lấy danh sách tài khoản từ TẤT CẢ nguồn
                        # 1. Tài khoản thủ công
                        manual_acc_list = manager.list_accounts()
                        for acc in manual_acc_list:
                            if 'service' not in acc:
                                acc['service'] = ''
                            acc['source'] = 'manual'
                    
                        # 2. Tài khoản từ BitLaunch
                        bitlaunch_apis = manager.list_bitlaunch_apis(config.user_id)
                        bitlaunch_acc_list = []
                        for api in bitlaunch_apis:
                            acc = {
                                'id': f"bitlaunch_{api['id']}",
                                'username': api['email'],
                                'service': 'BitLaunch',
                                'expiry': None,
                                'balance': api.get('balance', 0),
                                'source': 'bitlaunch'
                            }
                            bitlaunch_acc_list.append(acc)
                    
                        # 3. Tài khoản từ ZingProxy
                        zingproxy_acc_list = manager.list_zingproxy_accounts(config.user_id)
                        for acc in zingproxy_acc_list:
                            acc['source'] = 'zingproxy'
                            acc['username'] = acc.get('email', 'N/A')
                            acc['service'] = 'ZingProxy'
                            acc['expiry'] = None
                            acc['balance'] = acc.get('balance', 0)
                    
                        # 4. Tài khoản từ CloudFly
                        cloudfly_apis = manager.list_cloudfly_apis(config.user_id)
                        cloudfly_acc_list = []
                        for api in cloudfly_apis:
                            acc = {
                                'id': f"cloudfly_{api['id']}",
                                'username': api['email'],
                                'service': 'CloudFly',
                                'expiry': None,
                                'balance': api.get('balance', 0),
                                'source': 'cloudfly'
                            }
                            cloudfly_acc_list.append(acc)
                    
                        # Kết hợp tất cả tài khoản
                        all_accounts = manual_acc_list + bitlaunch_acc_list + zingproxy_acc_list + cloudfly_acc_list
                    
                        logger.info(f"[Scheduler] 📊 Found {len(all_accounts)} total accounts:")
                        logger.info(f"[Scheduler]   - Manual: {len(manual_acc_list)}")
                        logger.info(f"[Scheduler]   - BitLaunch: {len(bitlaunch_acc_list)}")
                        logger.info(f"[Scheduler]   - ZingProxy: {len(zingproxy_acc_list)}")
                        logger.info(f"[Scheduler]   - CloudFly: {len(cloudfly_acc_list)}")
                        
                        # Kiểm tra balance thấp
                        low_balance_count = 0
                        for acc in all_accounts:
                            balance = acc.get('balance', 0)
                            source = acc.get('source', '')
                            if source == 'bitlaunch' and balance < 5:
                                low_balance_count += 1
                                logger.warning(f"[Scheduler] 💰 BitLaunch low balance: {acc.get('username')} (${balance:.2f} < $5)")
                            elif source == 'zingproxy' and balance < 100000:
                                low_balance_count += 1
                                logger.warning(f"[Scheduler] 💰 ZingProxy low balance: {acc.get('username')} ({balance:,.0f} VND < 100,000 VND)")
                            elif source == 'cloudfly' and balance < 100000:
                                low_balance_count += 1
                                logger.warning(f"[Scheduler] 💰 CloudFly low balance: {acc.get('username')} ({balance:,.0f} VND < 100,000 VND)")
                        
                        logger.info(f"[Scheduler] 🚨 Found {low_balance_count} accounts with low balance")
                    
                        # Gửi thông báo cảnh báo (bao gồm cả balance thấp và tài khoản sắp hết hạn)
                        alert_success = send_account_expiry_notification(
                            room_id=config.room_id,
                            auth_token=config.auth_token,
                            user_id=config.user_id_rocket,
                            accounts=all_accounts,
                            warning_days=user.notify_days or 7
                        )
                    
                        if alert_success:
                            logger.info(f"[Scheduler] ✅ Alert sent successfully to user {user.username}")
                        else:
                            logger.error(f"[Scheduler] ❌ Failed to send alert to user {user.username}")
                        
                    except Exception as e:
                        logger.error(f"[Scheduler] ❌ Error processing user {config.id}: {e}")
                        continue
                
                logger.info("=" * 70)
                logger.info("[Scheduler] 🏁 Account alerts check completed")
                logger.info("=" * 70)
                
            except Exception as e:
                logger.error(f"[Scheduler] ❌ Error in check_account_alerts_5min: {e}")

    def send_daily_rocket_chat_notifications():
        """Gửi thông báo hàng ngày đến Rocket Chat cho tất cả users có cấu hình"""
        with app.app_context():
            try:
                from core.models import RocketChatConfig, User
                from core.rocket_chat import send_daily_account_summary, send_account_expiry_notification, send_detailed_account_info
                from core import manager
                
                logger.info("[Scheduler] Starting daily Rocket Chat notifications")
                
                # Lấy tất cả cấu hình Rocket Chat
                configs = RocketChatConfig.query.filter_by(is_active=True).all()
                
                if not configs:
                    logger.info("[Scheduler] No Rocket Chat configurations found")
                    return
                
                logger.info(f"[Scheduler] Found {len(configs)} Rocket Chat configurations")
                
                for config in configs:
                    try:
                        user = User.query.get(config.user_id)
                        if not user:
                            logger.warning(f"[Scheduler] User {config.user_id} not found for config {config.id}")
                            continue
                    
                        logger.info(f"[Scheduler] Processing notifications for user {user.username}")
                    
                        # Lấy danh sách tài khoản từ TẤT CẢ nguồn (giống như API endpoints)
                        # 1. Tài khoản thủ công
                        manual_acc_list = manager.list_accounts()
                        for acc in manual_acc_list:
                            if 'service' not in acc:
                                acc['service'] = ''
                            acc['source'] = 'manual'  # Đánh dấu nguồn
                    
                        # 2. Tài khoản từ BitLaunch
                        bitlaunch_apis = manager.list_bitlaunch_apis(config.user_id)
                        bitlaunch_acc_list = []
                        for api in bitlaunch_apis:
                            acc = {
                                'id': f"bitlaunch_{api['id']}",
                                'username': api['email'],
                                'service': 'BitLaunch',
                                'expiry': None,  # BitLaunch không có expiry
                                'balance': api.get('balance', 0),
                                'source': 'bitlaunch'
                            }
                            bitlaunch_acc_list.append(acc)
                    
                        # 3. Tài khoản từ ZingProxy
                        zingproxy_acc_list = manager.list_zingproxy_accounts(config.user_id)
                        for acc in zingproxy_acc_list:
                            acc['source'] = 'zingproxy'  # Đánh dấu nguồn
                            # Map fields để phù hợp với UI
                            acc['username'] = acc.get('email', 'N/A')
                            acc['service'] = 'ZingProxy'
                            acc['expiry'] = None  # ZingProxy không có expiry
                            acc['balance'] = acc.get('balance', 0)  # Thêm balance
                    
                        # 4. Tài khoản từ CloudFly
                        cloudfly_apis = manager.list_cloudfly_apis(config.user_id)
                        cloudfly_acc_list = []
                        for api in cloudfly_apis:
                            acc = {
                                'id': f"cloudfly_{api['id']}",
                                'username': api['email'],
                                'service': 'CloudFly',
                                'expiry': None,  # CloudFly không có expiry
                                'balance': api.get('balance', 0),
                                'source': 'cloudfly'
                            }
                            cloudfly_acc_list.append(acc)
                    
                        # Kết hợp tất cả tài khoản
                        all_accounts = manual_acc_list + bitlaunch_acc_list + zingproxy_acc_list + cloudfly_acc_list
                        
                        logger.info(f"[Scheduler] Found {len(all_accounts)} total accounts for user {user.username}:")
                        logger.info(f"[Scheduler]   - Manual: {len(manual_acc_list)}")
                        logger.info(f"[Scheduler]   - BitLaunch: {len(bitlaunch_acc_list)}")
                        logger.info(f"[Scheduler]   - ZingProxy: {len(zingproxy_acc_list)}")
                        logger.info(f"[Scheduler]   - CloudFly: {len(cloudfly_acc_list)}")
                    
                        # Gửi báo cáo tổng hợp hàng ngày
                        daily_success = send_daily_account_summary(
                            room_id=config.room_id,
                            auth_token=config.auth_token,  # Sử dụng trực tiếp
                            user_id=config.user_id_rocket,
                            accounts=all_accounts  # Sử dụng danh sách đầy đủ
                        )
                        
                        if daily_success:
                            logger.info(f"[Scheduler] Daily summary sent successfully for user {user.username}")
                        else:
                            logger.error(f"[Scheduler] Failed to send daily summary for user {user.username}")
                    
                        # Gửi thông báo tài khoản sắp hết hạn
                        expiry_success = send_account_expiry_notification(
                            room_id=config.room_id,
                            auth_token=config.auth_token,  # Sử dụng trực tiếp
                            user_id=config.user_id_rocket,
                            accounts=all_accounts,  # Sử dụng danh sách đầy đủ
                            warning_days=user.notify_days or 7
                        )
                        
                        if expiry_success:
                            logger.info(f"[Scheduler] Expiry notification sent successfully for user {user.username}")
                        else:
                            logger.error(f"[Scheduler] Failed to send expiry notification for user {user.username}")
                            
                    except Exception as e:
                        logger.error(f"[Scheduler] Error processing notifications for config {config.id}: {e}")
                        continue
            
                logger.info("[Scheduler] Daily Rocket Chat notifications completed")
                
            except Exception as e:
                logger.error(f"[Scheduler] Error in daily Rocket Chat notifications: {e}")

    # Lên lịch gửi cảnh báo hết hạn mỗi 5 phút để kiểm tra notify_hour của từng user
    scheduler.add_job(send_expiry_warnings, 'interval', minutes=5, id='expiry_warnings')
    
    # Lên lịch gửi báo cáo tổng hợp mỗi 5 phút để kiểm tra notify_hour của từng user
    scheduler.add_job(send_daily_summary, 'interval', minutes=5, id='daily_summary')
    
    # Lên lịch kiểm tra và gửi cảnh báo tài khoản mỗi 12 giờ
    # Job này sẽ gửi thông báo ngay lập tức, không cần chờ đến notify_hour
    scheduler.add_job(check_account_alerts_5min, 'interval', hours=12, id='account_alerts_12h')
    
    # Lên lịch gửi báo cáo tuần vào chủ nhật lúc 10h sáng
    scheduler.add_job(send_weekly_report, 'cron', day_of_week='sun', hour=10, minute=0, id='weekly_report')
    
    # Lên lịch gửi thông báo hàng ngày đến Rocket Chat mỗi ngày lúc 9h sáng
    scheduler.add_job(send_daily_rocket_chat_notifications, 'cron', hour=9, minute=0, id='rocketchat_daily_notifications')
    
    # ========================================================================
    # BITLAUNCH API UPDATES
    # ========================================================================
    # Cập nhật hàng ngày lúc 6h sáng
    scheduler.add_job(update_bitlaunch_apis, 'cron', hour=6, minute=0, id='bitlaunch_update')
    scheduler.add_job(update_bitlaunch_vps, 'cron', hour=6, minute=30, id='bitlaunch_vps_update')
    
    # Cập nhật mỗi 6 giờ để đảm bảo dữ liệu luôn mới (NEW!)
    scheduler.add_job(update_bitlaunch_apis, 'interval', hours=6, id='bitlaunch_update_interval')
    scheduler.add_job(update_bitlaunch_vps, 'interval', hours=6, id='bitlaunch_vps_update_interval')
    
    # ========================================================================
    # ZINGPROXY API UPDATES
    # ========================================================================
    # Cập nhật balance hàng ngày lúc 7h sáng
    scheduler.add_job(update_zingproxy_accounts, 'cron', hour=7, minute=0, id='zingproxy_update')
    
    # Cập nhật balance mỗi 6 giờ để đảm bảo dữ liệu luôn mới
    scheduler.add_job(update_zingproxy_accounts, 'interval', hours=6, id='zingproxy_update_interval')
    
    # Đồng bộ proxy mỗi 2 giờ (thường xuyên hơn vì proxy thay đổi nhiều)
    scheduler.add_job(auto_sync_zingproxy_proxies, 'interval', hours=2, id='zingproxy_proxy_sync')
    
    # Đồng bộ proxy tổng quát vào 2h sáng (khi ít traffic)
    scheduler.add_job(auto_sync_zingproxy_proxies, 'cron', hour=2, minute=0, id='zingproxy_proxy_sync_nightly')
    
    # ========================================================================
    # CLOUDFLY API UPDATES
    # ========================================================================
    # Cập nhật hàng ngày lúc 8h sáng
    scheduler.add_job(update_cloudfly_apis, 'cron', hour=8, minute=0, id='cloudfly_update')
    scheduler.add_job(update_cloudfly_vps, 'cron', hour=8, minute=30, id='cloudfly_vps_update')
    
    # Cập nhật mỗi 6 giờ để đảm bảo dữ liệu luôn mới
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