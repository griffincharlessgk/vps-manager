from typing import List, Dict, Optional
from datetime import datetime
from core.models import User, RocketChatConfig
from core.rocket_chat import send_account_expiry_notification, send_daily_account_summary
import logging
from core import manager

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

def notify_expiry_rocketchat_per_user(items: List[Dict], item_type: str, user: User, config: RocketChatConfig) -> None:
    """Gửi thông báo hết hạn qua RocketChat cho user cụ thể"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.info(f"[Notifier] Checking RocketChat notifications for {user.username} at {current_hour:02d}:{current_minute:02d}")
    
    # Kiểm tra xem có phải giờ và phút gửi thông báo của user này không
    if user.notify_hour != current_hour or user.notify_minute != current_minute:
        logger.debug(f"[Notifier] User {user.username} notify time: {user.notify_hour:02d}:{user.notify_minute:02d}, current: {current_hour:02d}:{current_minute:02d}")
        return
        
    logger.info(f"[Notifier] Gửi thông báo RocketChat cho user {user.username} lúc {current_hour:02d}:{current_minute:02d}")
    
    # Lọc items sắp hết hạn theo notify_days của user
    expiring_items = []
    for item in items:
        days_left = calculate_days_until_expiry(item.get('expiry'))
        if days_left is not None and days_left <= user.notify_days:
            expiring_items.append(item)
    
    logger.info(f"[Notifier] Found {len(expiring_items)} expiring items for user {user.username}")
    
    if expiring_items:
        # Gửi thông báo chi tiết về items sắp hết hạn
        try:
            success = send_account_expiry_notification(
                room_id=config.room_id,
                auth_token=config.auth_token,
                user_id=config.user_id_rocket,
                accounts=expiring_items,
                warning_days=user.notify_days
            )
            
            if success:
                logger.info(f"[Notifier] Successfully sent expiry notification to {user.username}")
            else:
                logger.error(f"[Notifier] Failed to send expiry notification to {user.username}")
        except Exception as e:
            logger.error(f"[Notifier] Error sending expiry notification to {user.username}: {e}")
    else:
        # Gửi thông báo không có items sắp hết hạn
        try:
            no_expiry_message = f"✅ **{item_type.upper()} - KHÔNG CÓ ITEMS SẮP HẾT HẠN**\n\n"
            no_expiry_message += f"👤 **User:** {user.username}\n"
            no_expiry_message += f"📅 **Ngày:** {datetime.now().strftime('%d/%m/%Y')}\n"
            no_expiry_message += f"⏰ **Giờ:** {datetime.now().strftime('%H:%M')}\n\n"
            no_expiry_message += f"🎉 Tất cả {item_type.lower()} của bạn đều còn hạn sử dụng!"
            
            # Sử dụng hàm gửi thông báo đơn giản
            from core.rocket_chat import send_formatted_notification_simple
            success = send_formatted_notification_simple(
                room_id=config.room_id,
                title=f"{item_type} - Không có cảnh báo",
                text=no_expiry_message,
                auth_token=config.auth_token,
                user_id=config.user_id_rocket,
                color="good"
            )
            
            if success:
                logger.info(f"[Notifier] Successfully sent no-expiry notification to {user.username}")
            else:
                logger.error(f"[Notifier] Failed to send no-expiry notification to {user.username}")
        except Exception as e:
            logger.error(f"[Notifier] Error sending no-expiry notification to {user.username}: {e}")

def send_daily_summary_rocketchat(user: User, config: RocketChatConfig) -> None:
    """Gửi báo cáo tổng hợp hàng ngày qua RocketChat"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.info(f"[Notifier] send_daily_summary_rocketchat called for user {user.username}")
    
    # Kiểm tra xem có phải giờ và phút gửi thông báo của user không
    if user.notify_hour != current_hour or user.notify_minute != current_minute:
        logger.debug(f"[Notifier] User {user.username} daily summary time: {user.notify_hour:02d}:{user.notify_minute:02d}, current: {current_hour:02d}:{current_minute:02d}")
        return
        
    logger.info(f"[Notifier] Gửi daily summary RocketChat cho user {user.username} lúc {current_hour:02d}:{current_minute:02d}")
    
    try:
        # Lấy danh sách tài khoản từ TẤT CẢ nguồn
        # 1. Tài khoản thủ công
        manual_acc_list = manager.list_accounts()
        for acc in manual_acc_list:
            if 'service' not in acc:
                acc['service'] = ''
            acc['source'] = 'manual'
        
        # 2. Tài khoản từ BitLaunch
        bitlaunch_apis = manager.list_bitlaunch_apis(user.id)
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
        zingproxy_acc_list = manager.list_zingproxy_accounts(user.id)
        for acc in zingproxy_acc_list:
            acc['source'] = 'zingproxy'
            acc['username'] = acc.get('email', 'N/A')
            acc['service'] = 'ZingProxy'
            acc['expiry'] = None
            acc['balance'] = acc.get('balance', 0)
        
        # 4. Tài khoản từ CloudFly
        cloudfly_apis = manager.list_cloudfly_apis(user.id)
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
        
        logger.info(f"[Notifier] Retrieved {len(all_accounts)} total accounts for user {user.username}")
        
        # Gửi báo cáo tổng hợp
        success = send_daily_account_summary(
            room_id=config.room_id,
            auth_token=config.auth_token,
            user_id=config.user_id_rocket,
            accounts=all_accounts
        )
        
        if success:
            logger.info(f"[Notifier] Successfully sent daily summary to {user.username}")
        else:
            logger.error(f"[Notifier] Failed to send daily summary to {user.username}")
            
    except Exception as e:
        logger.error(f"[Notifier] Error in send_daily_summary_rocketchat for {user.username}: {e}")

# Legacy functions - giữ lại để tương thích ngược
def notify_expiry_telegram_per_user(items: List[Dict], item_type: str) -> None:
    """Legacy function - chuyển hướng sang RocketChat"""
    logger.warning("[Notifier] notify_expiry_telegram_per_user is deprecated, use RocketChat instead")
    pass

def send_daily_summary(user) -> None:
    """Legacy function - chuyển hướng sang RocketChat"""
    logger.warning("[Notifier] send_daily_summary is deprecated, use RocketChat instead")
    pass