from typing import List, Dict, Optional
from datetime import datetime
from core.telegram_notify import send_telegram_message
import os
from dotenv import load_dotenv
from core.models import User
import logging
from core import manager

logger = logging.getLogger(__name__)

load_dotenv()  # Tải biến môi trường từ file .env

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

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

def notify_expiry_telegram_per_user(items: List[Dict], item_type: str) -> None:
    """Gửi thông báo hết hạn cho từng user theo giờ và phút của họ"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.info(f"[Notifier] Checking notifications for {current_hour:02d}:{current_minute:02d}")
    
    # Lấy tất cả users có telegram_chat_id
    users = User.query.filter(User.telegram_chat_id.isnot(None)).all()
    logger.info(f"[Notifier] Found {len(users)} users with telegram_chat_id")
    
    for user in users:
        # Kiểm tra xem có phải giờ và phút gửi thông báo của user này không
        if user.notify_hour != current_hour or user.notify_minute != current_minute:
            logger.debug(f"[Notifier] User {user.username} notify time: {user.notify_hour:02d}:{user.notify_minute:02d}, current: {current_hour:02d}:{current_minute:02d}")
            continue
            
        logger.info(f"[Notifier] Gửi thông báo cho user {user.username} lúc {current_hour:02d}:{current_minute:02d}")
        
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
            success = send_telegram_message(os.getenv('TELEGRAM_TOKEN'), user.telegram_chat_id, message)
            if success:
                logger.info(f"[Notifier] Successfully sent expiry notification to {user.username}")
            else:
                logger.error(f"[Notifier] Failed to send expiry notification to {user.username}")
        else:
            # Gửi thông báo thông thường nếu không có items sắp hết hạn
            message = f"✅ **THÔNG BÁO VPS MANAGER**\n\n"
            message += f"👤 **User:** {user.username}\n"
            message += f"📅 **Ngày:** {now.strftime('%d/%m/%Y %H:%M')}\n\n"
            message += f"✅ Không có items nào sắp hết hạn trong vòng {user.notify_days} ngày tới."
            success = send_telegram_message(os.getenv('TELEGRAM_TOKEN'), user.telegram_chat_id, message)
            if success:
                logger.info(f"[Notifier] Successfully sent no-expiry notification to {user.username}")
            else:
                logger.error(f"[Notifier] Failed to send no-expiry notification to {user.username}")

def send_daily_summary(user, force=False) -> None:
    """Gửi báo cáo tổng hợp hàng ngày cho user theo giờ và phút của họ"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.info(f"[Notifier] send_daily_summary called for user {user.username}, force={force}")
    
    # Kiểm tra xem có phải giờ và phút gửi thông báo của user không
    if not force and (user.notify_hour != current_hour or user.notify_minute != current_minute):
        logger.debug(f"[Notifier] User {user.username} daily summary time: {user.notify_hour:02d}:{user.notify_minute:02d}, current: {current_hour:02d}:{current_minute:02d}")
        return
        
    logger.info(f"[Notifier] Gửi daily summary cho user {user.username} lúc {current_hour:02d}:{current_minute:02d}")
    
    if not user.telegram_chat_id:
        logger.warning(f"[Notifier] User {user.username} has no telegram_chat_id")
        return
    
    logger.info(f"[Notifier] User {user.username} has telegram_chat_id: {user.telegram_chat_id}")
    
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
        logger.info(f"[Notifier] Sending message to telegram_chat_id: {user.telegram_chat_id}")
        
        token = os.getenv('TELEGRAM_TOKEN')
        logger.info(f"[Notifier] Using token: {token[:10] if token else 'None'}...")
        
        success = send_telegram_message(token, user.telegram_chat_id, message)
        if success:
            logger.info(f"[Notifier] Successfully sent daily summary to {user.username}")
        else:
            logger.error(f"[Notifier] Failed to send daily summary to {user.username}")
            
    except Exception as e:
        logger.error(f"[Notifier] Exception in send_daily_summary: {e}")
        raise e

