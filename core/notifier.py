from typing import List, Dict, Optional
from datetime import datetime
from core.models import User
import logging
from core import manager
from core.rocket_chat import send_formatted_notification_simple

logger = logging.getLogger(__name__)



def calculate_days_until_expiry(expiry_str: str) -> Optional[int]:
    """Tính số ngày còn lại đến khi hết hạn"""
    if not expiry_str:
        return None
    try:
        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        days_left = (expiry_date - today).days
        return days_left
    except:
        return None

def format_expiry_message_for_user(items: List[Dict], item_type: str, user) -> str:
    """Format thông báo hết hạn cho user cụ thể"""
    if not items:
        return ""
    
    message = f"⚠️ **CẢNH BÁO HẾT HẠN - {item_type.upper()}** ⚠️\n\n"
    message += f"👤 **User:** {user.username}\n"
    message += f"📅 **Ngày:** {datetime.now().strftime('%d/%m/%Y')}\n\n"
    
    for item in items:
        days_left = calculate_days_until_expiry(item.get('expiry'))
        if days_left is not None:
            if days_left < 0:
                message += f"❌ **{item.get('name', 'Unknown')}** - Đã quá hạn {abs(days_left)} ngày\n"
            elif days_left == 0:
                message += f"🚨 **{item.get('name', 'Unknown')}** - HẾT HẠN HÔM NAY!\n"
            elif days_left <= 3:
                message += f"🔶 **{item.get('name', 'Unknown')}** - Còn {days_left} ngày\n"
            else:
                message += f"📅 **{item.get('name', 'Unknown')}** - Còn {days_left} ngày\n"
    
    # Thêm thông tin user
    message += f"\n\n👤 **Người nhận:** {user.username}"
    if user.role == 'admin':
        message += " (Admin)"
    return message

def format_expiry_message(item: Dict, days_left: int, item_type: str, user: User) -> str:
    """Tạo nội dung thông báo cá nhân hóa, có đếm ngược"""
    name = item.get('name') or item.get('username') or item.get('id')
    service = item.get('service', 'Unknown')
    ip = item.get('ip', 'N/A')
    expiry_date = item.get('expiry')
    # Tính thời gian đếm ngược
    countdown_str = ''
    if expiry_date:
        try:
            dt_expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            now = datetime.now()
            delta = dt_expiry - now
            total_seconds = int(delta.total_seconds())
            if total_seconds > 0:
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                minutes = (total_seconds % 3600) // 60
                countdown_str = f"\n⏳ Thời gian còn lại: {days} ngày {hours} giờ {minutes} phút"
        except Exception:
            pass
    # Template cơ bản
    template = f"⚠️ **CẢNH BÁO HẾT HẠN** ⚠️\n\n"
    template += f"🔸 **Loại:** {item_type}\n"
    template += f"🔸 **Tên:** {name}\n"
    template += f"🔸 **Dịch vụ:** {service}\n"
    if ip and ip != 'N/A':
        template += f"🔸 **IP:** {ip}\n"
    template += f"🔸 **Ngày hết hạn:** {expiry_date}\n"
    template += f"🔸 **Còn lại:** {days_left} ngày{countdown_str}\n\n"
    # Thêm cảnh báo theo số ngày
    if days_left == 0:
        template += "🚨 **HẾT HẠN HÔM NAY!** 🚨\n"
        template += "Vui lòng gia hạn ngay để tránh gián đoạn dịch vụ."
    elif days_left == 1:
        template += "⚠️ **HẾT HẠN NGÀY MAI!** ⚠️\n"
        template += "Cần gia hạn gấp để duy trì dịch vụ."
    elif days_left <= 3:
        template += "🔶 **HẾT HẠN TRONG VÀI NGÀY TỚI** 🔶\n"
        template += "Vui lòng kiểm tra và gia hạn sớm."
    else:
        template += "📅 **SẮP HẾT HẠN** 📅\n"
        template += "Nhắc nhở gia hạn dịch vụ."
    # Thêm thông tin user
    template += f"\n\n👤 **Người nhận:** {user.username}"
    if user.role == 'admin':
        template += " (Admin)"
    return template

def notify_expiry_per_user(items: List[Dict], item_type: str, force: bool = False) -> None:
    """Gửi thông báo hết hạn theo giờ/phút của từng user qua Rocket.Chat"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.info(f"[Notifier] Checking notifications for {current_hour:02d}:{current_minute:02d}, force={force}")
    
    # Lấy tất cả users (sẽ lọc theo cấu hình Rocket.Chat)
    users = User.query.all()
    logger.info(f"[Notifier] Found {len(users)} users to check Rocket.Chat config")
    
    for user in users:
        # Nếu không phải force mode, kiểm tra giờ gửi thông báo
        if not force:
            if user.notify_hour != current_hour or user.notify_minute != current_minute:
                logger.debug(f"[Notifier] User {user.username} notify time: {user.notify_hour:02d}:{user.notify_minute:02d}, current: {current_hour:02d}:{current_minute:02d}")
                continue
                
        logger.info(f"[Notifier] Gửi thông báo Rocket.Chat cho user {user.username} lúc {current_hour:02d}:{current_minute:02d} (force={force})")
        config = manager.get_rocket_chat_config(user.id)
        if not config:
            logger.warning(f"[Notifier] User {user.username} chưa cấu hình Rocket.Chat")
            continue
        
        # Lọc items sắp hết hạn theo notify_days của user
        expiring_items = []
        for item in items:
            days_left = calculate_days_until_expiry(item.get('expiry'))
            if days_left is not None and days_left <= user.notify_days:
                expiring_items.append(item)
        
        logger.info(f"[Notifier] Found {len(expiring_items)} expiring items for user {user.username}")
        
        if expiring_items:
            # Gửi thông báo chi tiết về items sắp hết hạn
            message = format_expiry_message_for_user(expiring_items, item_type, user)
            success = send_formatted_notification_simple(
                room_id=config.room_id,
                title=f"Cảnh báo hết hạn - {item_type}",
                text=message,
                auth_token=config.auth_token,
                user_id=config.user_id_rocket,
                color="warning"
            )
            if success:
                logger.info(f"[Notifier] Successfully sent Rocket.Chat expiry notification to {user.username}")
            else:
                logger.error(f"[Notifier] Failed to send Rocket.Chat expiry notification to {user.username}")
        else:
            # Gửi thông báo thông thường nếu không có items sắp hết hạn
            message = f"✅ **THÔNG BÁO VPS MANAGER**\n\n"
            message += f"👤 **User:** {user.username}\n"
            message += f"📅 **Ngày:** {now.strftime('%d/%m/%Y %H:%M')}\n\n"
            message += f"✅ Không có items nào sắp hết hạn trong vòng {user.notify_days} ngày tới."
            success = send_formatted_notification_simple(
                room_id=config.room_id,
                title="Thông báo hệ thống",
                text=message,
                auth_token=config.auth_token,
                user_id=config.user_id_rocket,
                color="good"
            )
            if success:
                logger.info(f"[Notifier] Successfully sent Rocket.Chat no-expiry notification to {user.username}")
            else:
                logger.error(f"[Notifier] Failed to send Rocket.Chat no-expiry notification to {user.username}")

def send_daily_summary_for_user_old(user, force=False) -> None:
    """Gửi báo cáo tổng hợp hàng ngày cho user theo giờ/phút, qua Rocket.Chat"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.info(f"[Notifier] send_daily_summary called for user {user.username}, force={force}")
    
    # Kiểm tra xem có phải giờ và phút gửi thông báo của user không
    if not force and (user.notify_hour != current_hour or user.notify_minute != current_minute):
        logger.debug(f"[Notifier] User {user.username} daily summary time: {user.notify_hour:02d}:{user.notify_minute:02d}, current: {current_hour:02d}:{current_minute:02d}")
        return
        
    logger.info(f"[Notifier] Gửi daily summary Rocket.Chat cho user {user.username} lúc {current_hour:02d}:{current_minute:02d}")
    
    config = manager.get_rocket_chat_config(user.id)
    if not config:
        logger.warning(f"[Notifier] User {user.username} chưa cấu hình Rocket.Chat")
        return
    
    try:
        vps_list = manager.list_vps()
        acc_list = manager.list_accounts()
        logger.info(f"[Notifier] Retrieved {len(vps_list)} VPS and {len(acc_list)} accounts")
        
        # Tạo báo cáo tổng hợp
        total_vps = len(vps_list)
        total_accounts = len(acc_list)
        
        expiring_vps = [v for v in vps_list if calculate_days_until_expiry(v.get('expiry')) <= 7]
        expiring_accounts = [a for a in acc_list if calculate_days_until_expiry(a.get('expiry')) <= 7]
        
        logger.info(f"[Notifier] Found {len(expiring_vps)} expiring VPS and {len(expiring_accounts)} expiring accounts")
        
        message = f"""📊 **BÁO CÁO TỔNG HỢP HÀNG NGÀY**

👤 **User:** {user.username}
📅 **Ngày:** {now.strftime('%d/%m/%Y')}
⏰ **Giờ:** {now.strftime('%H:%M')}

🖥️ **VPS:** {total_vps} máy chủ
📋 **Account:** {total_accounts} tài khoản

⚠️ **Sắp hết hạn (7 ngày):**
• VPS: {len(expiring_vps)} máy chủ
• Account: {len(expiring_accounts)} tài khoản

🔔 **Cài đặt thông báo:**
• Số ngày cảnh báo: {user.notify_days} ngày
• Giờ gửi thông báo: {user.notify_hour}:00

💡 **Lưu ý:** Kiểm tra và gia hạn các dịch vụ sắp hết hạn!"""
        
        logger.info(f"[Notifier] Message length: {len(message)} characters")
        success = send_formatted_notification_simple(
            room_id=config.room_id,
            title="📊 Báo cáo tổng hợp hàng ngày",
            text=message,
            auth_token=config.auth_token,
            user_id=config.user_id_rocket,
            color="good"
        )
        if success:
            logger.info(f"[Notifier] Successfully sent Rocket.Chat daily summary to {user.username}")
        else:
            logger.error(f"[Notifier] Failed to send Rocket.Chat daily summary to {user.username}")
            
    except Exception as e:
        logger.error(f"[Notifier] Exception in send_daily_summary: {e}")
        raise e

# Celery task methods
def send_daily_summary(vps_list: List[Dict], acc_list: List[Dict], 
                      bitlaunch_apis: List[Dict], zingproxy_apis: List[Dict], 
                      cloudfly_apis: List[Dict]) -> None:
    """Send daily summary for all users"""
    try:
        logger.info("Starting daily summary task")
        
        # Get all users
        users = User.query.all()
        logger.info(f"Found {len(users)} users for daily summary")
        
        for user in users:
            try:
                # Get user's Rocket.Chat config
                config = manager.get_rocket_chat_config(user.id)
                if not config:
                    logger.warning(f"User {user.username} has no Rocket.Chat config")
                    continue
                
                # Filter items for this user (if needed)
                user_vps = [vps for vps in vps_list if vps.get('user_id') == user.id] if vps_list else []
                user_accounts = [acc for acc in acc_list if acc.get('user_id') == user.id] if acc_list else []
                
                # Send daily summary
                send_daily_summary_for_user(user, user_vps, user_accounts, bitlaunch_apis, zingproxy_apis, cloudfly_apis, config)
                
            except Exception as e:
                logger.error(f"Error sending daily summary for user {user.username}: {str(e)}")
        
        logger.info("Daily summary task completed")
        
    except Exception as e:
        logger.error(f"Daily summary task failed: {str(e)}")
        raise

def send_daily_summary_for_user(user, vps_list, acc_list, bitlaunch_apis, zingproxy_apis, cloudfly_apis, config) -> None:
    """Send daily summary for specific user"""
    try:
        logger.info(f"Sending daily summary for user {user.username}")
        
        # Create combined account list
        all_accounts = []
        
        # Add manual accounts
        for acc in acc_list:
            if 'service' not in acc:
                acc['service'] = ''
            acc['source'] = 'manual'
            all_accounts.append(acc)
        
        # Add BitLaunch accounts
        for api in bitlaunch_apis:
            acc = {
                'id': f"bitlaunch_{api['id']}",
                'username': api['email'],
                'service': 'BitLaunch',
                'expiry': None,
                'balance': api.get('balance', 0),
                'source': 'bitlaunch'
            }
            all_accounts.append(acc)
        
        # Add ZingProxy accounts
        for acc in zingproxy_apis:
            acc['source'] = 'zingproxy'
            acc['username'] = acc.get('email', 'N/A')
            acc['service'] = 'ZingProxy'
            acc['expiry'] = None
            acc['balance'] = acc.get('balance', 0)
            all_accounts.append(acc)
        
        # Add CloudFly accounts
        for api in cloudfly_apis:
            acc = {
                'id': f"cloudfly_{api['id']}",
                'username': api['email'],
                'service': 'CloudFly',
                'expiry': None,
                'balance': api.get('balance', 0),
                'source': 'cloudfly'
            }
            all_accounts.append(acc)
        
        # Send daily summary via Rocket.Chat
        from core.rocket_chat import send_daily_account_summary
        success = send_daily_account_summary(
            room_id=config.room_id,
            auth_token=config.auth_token,
            user_id=config.user_id_rocket,
            accounts=all_accounts
        )
        
        if success:
            logger.info(f"Successfully sent daily summary for user {user.username}")
        else:
            logger.error(f"Failed to send daily summary for user {user.username}")
            
    except Exception as e:
        logger.error(f"Error sending daily summary for user {user.username}: {str(e)}")
        raise

def send_weekly_report(vps_list: List[Dict], acc_list: List[Dict], 
                      bitlaunch_apis: List[Dict], zingproxy_apis: List[Dict], 
                      cloudfly_apis: List[Dict], expiring_vps: int, 
                      expiring_accounts: int) -> None:
    """Send weekly report for all users"""
    try:
        logger.info("Starting weekly report task")
        
        # Get all users
        users = User.query.all()
        logger.info(f"Found {len(users)} users for weekly report")
        
        for user in users:
            try:
                # Get user's Rocket.Chat config
                config = manager.get_rocket_chat_config(user.id)
                if not config:
                    logger.warning(f"User {user.username} has no Rocket.Chat config")
                    continue
                
                # Send weekly report
                send_weekly_report_for_user(user, vps_list, acc_list, 
                                          bitlaunch_apis, zingproxy_apis, 
                                          cloudfly_apis, expiring_vps, 
                                          expiring_accounts, config)
                
            except Exception as e:
                logger.error(f"Error sending weekly report for user {user.username}: {str(e)}")
        
        logger.info("Weekly report task completed")
        
    except Exception as e:
        logger.error(f"Weekly report task failed: {str(e)}")
        raise

def send_weekly_report_for_user(user: User, vps_list: List[Dict], acc_list: List[Dict], 
                               bitlaunch_apis: List[Dict], zingproxy_apis: List[Dict], 
                               cloudfly_apis: List[Dict], expiring_vps: int, 
                               expiring_accounts: int, config) -> None:
    """Send weekly report for specific user"""
    try:
        now = datetime.now()
        
        # Calculate statistics
        total_vps = len(vps_list)
        total_accounts = len(acc_list)
        total_apis = len(bitlaunch_apis) + len(zingproxy_apis) + len(cloudfly_apis)
        
        message = f"""📊 **BÁO CÁO TUẦN**
        
👤 **User:** {user.username}
📅 **Tuần:** {now.strftime('%d/%m/%Y')}
⏰ **Giờ:** {now.strftime('%H:%M')}

📈 **THỐNG KÊ TỔNG QUAN:**
• VPS: {total_vps} máy chủ
• Account: {total_accounts} tài khoản
• API Keys: {total_apis} keys

⚠️ **CẢNH BÁO:**
• VPS sắp hết hạn: {expiring_vps} máy chủ
• Account sắp hết hạn: {expiring_accounts} tài khoản

🔑 **API KEYS:**
• BitLaunch: {len(bitlaunch_apis)} keys
• ZingProxy: {len(zingproxy_apis)} keys
• CloudFly: {len(cloudfly_apis)} keys

💡 **Lưu ý:** Kiểm tra và gia hạn các dịch vụ sắp hết hạn!"""
        
        success = send_formatted_notification_simple(
            room_id=config.room_id,
            title="📊 Báo cáo tuần",
            text=message,
            auth_token=config.auth_token,
            user_id=config.user_id_rocket,
            color="good"
        )
        
        if success:
            logger.info(f"Successfully sent weekly report to {user.username}")
        else:
            logger.error(f"Failed to send weekly report to {user.username}")
            
    except Exception as e:
        logger.error(f"Error sending weekly report for user {user.username}: {str(e)}")
        raise

def send_rocketchat_daily_notifications(vps_list: List[Dict], acc_list: List[Dict]) -> None:
    """Send Rocket.Chat daily notifications for all users"""
    try:
        logger.info("Starting Rocket.Chat daily notifications task")
        
        # Get all users
        users = User.query.all()
        logger.info(f"Found {len(users)} users for Rocket.Chat notifications")
        
        for user in users:
            try:
                # Get user's Rocket.Chat config
                config = manager.get_rocket_chat_config(user.id)
                if not config:
                    logger.warning(f"User {user.username} has no Rocket.Chat config")
                    continue
                
                # Filter items for this user (if needed)
                user_vps = [vps for vps in vps_list if vps.get('user_id') == user.id] if vps_list else []
                user_accounts = [acc for acc in acc_list if acc.get('user_id') == user.id] if acc_list else []
                
                # Send notifications
                notify_expiry_per_user(user_vps, item_type='VPS', force=True)
                notify_expiry_per_user(user_accounts, item_type='Account', force=True)
                
            except Exception as e:
                logger.error(f"Error sending Rocket.Chat notifications for user {user.username}: {str(e)}")
        
        logger.info("Rocket.Chat daily notifications task completed")
        
    except Exception as e:
        logger.error(f"Rocket.Chat daily notifications task failed: {str(e)}")
        raise

