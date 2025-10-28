import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RocketChatError(Exception):
    """Custom exception for Rocket Chat API errors"""
    pass

class RocketChatClient:
    """Client for interacting with Rocket Chat API"""
    
    def __init__(self, auth_token: str, user_id: str, base_url: str = "https://rocket.int.team"):
        self.auth_token = auth_token
        self.user_id = user_id
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-Auth-Token": auth_token,
            "X-User-Id": user_id,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Rocket Chat API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, verify=False)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, verify=False)
            else:
                raise RocketChatError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise RocketChatError(f"API request failed: {str(e)}")
        except Exception as e:
            raise RocketChatError(f"Unexpected error: {str(e)}")
    
    def get_channels(self) -> List[Dict]:
        """Get list of channels"""
        response = self._make_request('GET', '/api/v1/channels.list')
        return response.get('channels', [])
    
    def get_groups(self) -> List[Dict]:
        """Get list of groups"""
        response = self._make_request('GET', '/api/v1/groups.list')
        return response.get('groups', [])
    
    def send_message(self, room_id: str, message: str, alias: Optional[str] = None) -> Dict:
        """Send message to a room"""
        payload = {
            "roomId": room_id,
            "text": message
        }
        
        if alias:
            payload["alias"] = alias
            
        return self._make_request('POST', '/api/v1/chat.postMessage', payload)
    
    def send_formatted_message(self, room_id: str, title: str, text: str, color: str = "good") -> Dict:
        """Send formatted message with attachment"""
        payload = {
            "roomId": room_id,
            "attachments": [{
                "title": title,
                "text": text,
                "color": color,
                "ts": datetime.now().isoformat()
            }]
        }
        
        return self._make_request('POST', '/api/v1/chat.postMessage', payload)

# ==================== SIMPLE FUNCTIONS ====================

def send_formatted_notification_simple(
    room_id: str,
    title: str,
    text: str,
    auth_token: str,
    user_id: str,
    color: str = "good"
) -> bool:
    """Send formatted notification to Rocket Chat (simplified version)"""
    try:
        base_url = "https://rocket.int.team"
        headers = {
            "X-Auth-Token": auth_token,
            "X-User-Id": user_id,
            "Content-Type": "application/json"
        }
        
        payload = {
            "roomId": room_id,
            "attachments": [{
                "title": title,
                "text": text,
                "color": color,
                "ts": datetime.now().isoformat()
            }]
        }
        
        response = requests.post(f"{base_url}/api/v1/chat.postMessage", 
                               headers=headers, 
                               json=payload, 
                               verify=False)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"Rocket Chat notification sent successfully to room {room_id}")
                return True
            else:
                logger.error(f"Rocket Chat API returned error: {result}")
                return False
        else:
            logger.error(f"Rocket Chat API request failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error sending Rocket Chat notification: {e}")
        return False

def send_account_expiry_notification(
    room_id: str,
    auth_token: str,
    user_id: str,
    accounts: List[Dict],
    warning_days: int = 7,
    vps_list: List[Dict] = None
) -> bool:
    """Gửi thông báo VPS/tài khoản sắp hết hạn và balance thấp đến Rocket Chat"""
    try:
        logger.info(f"[RocketChat] Starting account/VPS expiry notification")
        logger.info(f"[RocketChat] Room ID: {room_id}, User ID: {user_id}, Warning days: {warning_days}")
        logger.info(f"[RocketChat] Total accounts received: {len(accounts) if accounts else 0}")
        logger.info(f"[RocketChat] Total VPS received: {len(vps_list) if vps_list else 0}")
        
        if not accounts and not vps_list:
            logger.info(f"[RocketChat] No accounts or VPS to process")
            return True
        
        # Log chi tiết từng account
        if accounts:
            for i, acc in enumerate(accounts):
                logger.info(f"[RocketChat] Account {i+1}: {acc}")
        
        # Lọc tài khoản và VPS sắp hết hạn
        today = datetime.now().date()
        expiring_accounts = []
        expired_accounts = []
        expiring_vps = []
        expired_vps = []
        
        # Kiểm tra VPS hết hạn
        if vps_list:
            logger.info(f"[RocketChat] Filtering expiring and expired VPS...")
            for vps in vps_list:
                logger.info(f"[RocketChat] Checking VPS: {vps.get('name', 'Unknown')} - Expiry: {vps.get('expiry', 'N/A')}")
                
                if vps.get('expiry'):
                    try:
                        expiry_date = datetime.strptime(vps['expiry'], '%Y-%m-%d').date()
                        days_left = (expiry_date - today).days
                        logger.info(f"[RocketChat] VPS {vps.get('name')}: expiry_date={expiry_date}, days_left={days_left}")
                        
                        if days_left < 0:
                            expired_vps.append({
                                'item': vps,
                                'days_left': days_left,
                                'type': 'expired_vps'
                            })
                            logger.info(f"[RocketChat] Added to expired VPS list: {vps.get('name')} (đã hết hạn {abs(days_left)} ngày)")
                        elif 0 <= days_left <= warning_days:
                            expiring_vps.append({
                                'item': vps,
                                'days_left': days_left,
                                'type': 'expiry_vps'
                            })
                            logger.info(f"[RocketChat] Added to expiring VPS list: {vps.get('name')} (còn {days_left} ngày)")
                    except Exception as e:
                        logger.error(f"[RocketChat] Error parsing expiry date for VPS {vps.get('name')}: {e}")
                        continue
            
            logger.info(f"[RocketChat] Found {len(expiring_vps)} expiring VPS and {len(expired_vps)} expired VPS")
        
        logger.info(f"[RocketChat] Filtering expiring and expired accounts (manual only)...")
        for account in accounts:
            logger.info(f"[RocketChat] Checking account: {account.get('username', 'Unknown')} - Source: {account.get('source', 'N/A')} - Expiry: {account.get('expiry', 'N/A')}")
            
            if account.get('source') == 'manual' and account.get('expiry'):
                try:
                    expiry_date = datetime.strptime(account['expiry'], '%Y-%m-%d').date()
                    days_left = (expiry_date - today).days
                    logger.info(f"[RocketChat] Manual account {account.get('username')}: expiry_date={expiry_date}, days_left={days_left}")
                    
                    if days_left < 0:
                        # Tài khoản đã hết hạn
                        expired_accounts.append({
                            'account': account,
                            'days_left': days_left,
                            'type': 'expired'
                        })
                        logger.info(f"[RocketChat] Added to expired list: {account.get('username')} (đã hết hạn {abs(days_left)} ngày)")
                    elif 0 <= days_left <= warning_days:
                        # Tài khoản sắp hết hạn
                        expiring_accounts.append({
                            'account': account,
                            'days_left': days_left,
                            'type': 'expiry'
                        })
                        logger.info(f"[RocketChat] Added to expiring list: {account.get('username')} (còn {days_left} ngày)")
                except Exception as e:
                    logger.error(f"[RocketChat] Error parsing expiry date for {account.get('username')}: {e}")
                    continue
        
        logger.info(f"[RocketChat] Found {len(expiring_accounts)} expiring accounts and {len(expired_accounts)} expired accounts")
        
        # Lọc tài khoản có balance thấp
        low_balance_accounts = []
        
        logger.info(f"[RocketChat] Filtering low balance accounts...")
        for account in accounts:
            source = account.get('source', 'unknown')
            balance = account.get('balance', 0)
            logger.info(f"[RocketChat] Checking balance for {account.get('username', 'Unknown')} - Source: {source} - Balance: ${balance}")
            
            if source == 'bitlaunch':
                if balance < 5:  # Cảnh báo khi balance < $5
                    low_balance_accounts.append({
                        'account': account,
                        'balance': balance,
                        'type': 'low_balance',
                        'threshold': 5
                    })
                    logger.info(f"[RocketChat] Added BitLaunch to low balance list: {account.get('username')} (${balance:.3f} < $5)")
            elif source == 'zingproxy':
                if balance < 100000:  # Cảnh báo khi balance < 100,000 VND
                    low_balance_accounts.append({
                        'account': account,
                        'balance': balance,
                        'type': 'low_balance',
                        'threshold': 100000
                    })
                    logger.info(f"[RocketChat] Added ZingProxy to low balance list: {account.get('username')} ({balance:,.0f} VND < 100,000 VND)")
            elif source == 'cloudfly':
                if balance < 100000:  # Cảnh báo khi balance < 100,000 VND
                    low_balance_accounts.append({
                        'account': account,
                        'balance': balance,
                        'type': 'low_balance',
                        'threshold': 100000
                    })
                    logger.info(f"[RocketChat] Added CloudFly to low balance list: {account.get('username')} ({balance:,.0f} VND < 100,000 VND)")
        
        logger.info(f"[RocketChat] Found {len(low_balance_accounts)} low balance accounts")
        
        # Kết hợp tất cả cảnh báo (VPS + Accounts)
        all_warnings = expired_vps + expiring_vps + expired_accounts + expiring_accounts + low_balance_accounts
        
        logger.info(f"[RocketChat] Total warnings: {len(all_warnings)} (expired_vps: {len(expired_vps)}, expiring_vps: {len(expiring_vps)}, expired: {len(expired_accounts)}, expiry: {len(expiring_accounts)}, low_balance: {len(low_balance_accounts)})")
        
        if not all_warnings:
            logger.info(f"[RocketChat] No warnings to send")
            return True
        
        # Tạo nội dung thông báo
        title = f"⚠️ Cảnh báo VPS/Tài khoản ({len(all_warnings)} cảnh báo)"
        
        text = f"**Danh sách cảnh báo VPS/Tài khoản:**\n\n"
        
        # Thông báo VPS đã hết hạn
        if expired_vps:
            text += f"🚨 **VPS đã hết hạn ({len(expired_vps)}):**\n"
            for item in expired_vps:
                vps = item['item']
                days_left = item['days_left']
                
                text += f"🚨 **{vps.get('name', vps.get('id', 'Unknown'))}**\n"
                text += f"   • IP: {vps.get('ip', 'N/A')}\n"
                text += f"   • Provider: {vps.get('provider', 'N/A')}\n"
                text += f"   • Ngày hết hạn: {vps.get('expiry', 'N/A')}\n"
                text += f"   • Trạng thái: Đã hết hạn {abs(days_left)} ngày\n\n"
        
        # Thông báo VPS sắp hết hạn
        if expiring_vps:
            text += f"📅 **VPS sắp hết hạn ({len(expiring_vps)}):**\n"
            for item in expiring_vps:
                vps = item['item']
                days_left = item['days_left']
                
                if days_left == 0:
                    status_emoji = "🚨"
                    status_text = "HẾT HẠN HÔM NAY!"
                elif days_left == 1:
                    status_emoji = "⚠️"
                    status_text = "Hết hạn ngày mai"
                else:
                    status_emoji = "📅"
                    status_text = f"Còn {days_left} ngày"
                
                text += f"{status_emoji} **{vps.get('name', vps.get('id', 'Unknown'))}**\n"
                text += f"   • IP: {vps.get('ip', 'N/A')}\n"
                text += f"   • Provider: {vps.get('provider', 'N/A')}\n"
                text += f"   • Ngày hết hạn: {vps.get('expiry', 'N/A')}\n"
                text += f"   • Trạng thái: {status_text}\n\n"
        
        # Thông báo tài khoản đã hết hạn
        if expired_accounts:
            text += f"🚨 **Tài khoản đã hết hạn ({len(expired_accounts)}):**\n"
            for item in expired_accounts:
                account = item['account']
                days_left = item['days_left']
                
                text += f"🚨 **{account.get('username', account.get('id', 'Unknown'))}**\n"
                text += f"   • Dịch vụ: {account.get('service', 'N/A')}\n"
                text += f"   • Ngày hết hạn: {account.get('expiry', 'N/A')}\n"
                text += f"   • Trạng thái: Đã hết hạn {abs(days_left)} ngày\n\n"
        
        # Thông báo tài khoản sắp hết hạn
        if expiring_accounts:
            text += f"📅 **Tài khoản sắp hết hạn ({len(expiring_accounts)}):**\n"
            for item in expiring_accounts:
                account = item['account']
                days_left = item['days_left']
                
                if days_left == 0:
                    status_emoji = "🚨"
                    status_text = "HẾT HẠN HÔM NAY!"
                elif days_left == 1:
                    status_emoji = "⚠️"
                    status_text = "Hết hạn ngày mai"
                else:
                    status_emoji = "📅"
                    status_text = f"Còn {days_left} ngày"
                
                text += f"{status_emoji} **{account.get('username', account.get('id', 'Unknown'))}**\n"
                text += f"   • Dịch vụ: {account.get('service', 'N/A')}\n"
                text += f"   • Ngày hết hạn: {account.get('expiry', 'N/A')}\n"
                text += f"   • Trạng thái: {status_text}\n\n"
        
        # Thông báo tài khoản có balance thấp
        if low_balance_accounts:
            text += f"💰 **Tài khoản có balance thấp ({len(low_balance_accounts)}):**\n"
            for item in low_balance_accounts:
                account = item['account']
                balance = item['balance']
                threshold = item['threshold']
                
                if balance < 2:
                    status_emoji = "🚨"
                    status_text = "BALANCE RẤT THẤP!"
                elif balance < threshold * 0.5:
                    status_emoji = "⚠️"
                    status_text = "Balance thấp"
                else:
                    status_emoji = "💰"
                    status_text = "Balance sắp thấp"
                
                text += f"{status_emoji} **{account.get('username', account.get('id', 'Unknown'))}**\n"
                text += f"   • Dịch vụ: {account.get('service', 'N/A')}\n"
                # Format balance dựa trên nguồn
                if account.get('source') in ['zingproxy', 'cloudfly']:
                    text += f"   • Balance hiện tại: {balance:,.0f} VND\n"
                    text += f"   • Ngưỡng cảnh báo: {threshold:,.0f} VND\n"
                else:
                    text += f"   • Balance hiện tại: ${balance:.2f}\n"
                    text += f"   • Ngưỡng cảnh báo: ${threshold}\n"
                text += f"   • Trạng thái: {status_text}\n\n"
        
        logger.info(f"[RocketChat] Notification content prepared:")
        logger.info(f"[RocketChat] Title: {title}")
        logger.info(f"[RocketChat] Text length: {len(text)} characters")
        
        # Chọn màu dựa trên mức độ nghiêm trọng
        has_expired = len(expired_accounts) > 0 or len(expired_vps) > 0  # VPS/Tài khoản đã hết hạn là nghiêm trọng nhất
        has_critical = has_expired or any(item.get('days_left') == 0 for item in expiring_accounts) or \
                      any(item.get('days_left') == 0 for item in expiring_vps) or \
                      any(item.get('balance', 0) < 2 for item in low_balance_accounts)
        has_warning = any(item.get('days_left') <= 1 for item in expiring_accounts) or \
                     any(item.get('balance', 0) < item.get('threshold', 0) * 0.5 for item in low_balance_accounts)
        
        if has_expired:
            color = "danger"  # Đỏ - tài khoản đã hết hạn
        elif has_critical:
            color = "danger"  # Đỏ - rất nghiêm trọng
        elif has_warning:
            color = "warning"  # Vàng - cảnh báo
        else:
            color = "info"  # Xanh - thông tin
        
        logger.info(f"[RocketChat] Selected color: {color} (expired: {has_expired}, critical: {has_critical}, warning: {has_warning})")
        
        # Gửi thông báo
        logger.info(f"[RocketChat] Sending notification to Rocket Chat...")
        result = send_formatted_notification_simple(
            room_id=room_id,
            title=title,
            text=text,
            auth_token=auth_token,
            user_id=user_id,
            color=color
        )
        
        logger.info(f"[RocketChat] send_formatted_notification_simple result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[RocketChat] Error sending account expiry notification: {e}")
        import traceback
        logger.error(f"[RocketChat] Traceback: {traceback.format_exc()}")
        return False

def send_detailed_account_info(
    room_id: str,
    auth_token: str,
    user_id: str,
    accounts: List[Dict]
) -> bool:
    """Gửi thông tin chi tiết tất cả tài khoản đến Rocket Chat"""
    try:
        logger.info(f"[RocketChat] Starting detailed account info notification")
        logger.info(f"[RocketChat] Room ID: {room_id}, User ID: {user_id}")
        logger.info(f"[RocketChat] Total accounts to report: {len(accounts) if accounts else 0}")
        
        if not accounts:
            logger.info(f"[RocketChat] No accounts to report")
            return True
        
        # Thống kê theo nguồn
        manual_accounts = [acc for acc in accounts if acc.get('source') == 'manual']
        bitlaunch_accounts = [acc for acc in accounts if acc.get('source') == 'bitlaunch']
        zingproxy_accounts = [acc for acc in accounts if acc.get('source') == 'zingproxy']
        cloudfly_accounts = [acc for acc in accounts if acc.get('source') == 'cloudfly']
        
        # Tính balance theo từng nguồn
        bitlaunch_balance = sum([acc.get('balance', 0) for acc in bitlaunch_accounts])
        zingproxy_balance = sum([acc.get('balance', 0) for acc in zingproxy_accounts])
        cloudfly_balance = sum([acc.get('balance', 0) for acc in cloudfly_accounts])
        
        # Tạo tiêu đề
        title = f"📊 Thông tin chi tiết tài khoản - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        # Tạo nội dung báo cáo
        text = f"**📈 Tổng quan hệ thống:**\n\n"
        text += f"🔢 **Tổng số tài khoản:** {len(accounts)}\n"
        text += f"   • 📝 Thủ công: {len(manual_accounts)}\n"
        text += f"   • 🚀 BitLaunch: {len(bitlaunch_accounts)}\n"
        text += f"   • 🌐 ZingProxy: {len(zingproxy_accounts)}\n"
        text += f"   • ☁️ CloudFly: {len(cloudfly_accounts)}\n\n"
        
        # Thông tin balance tổng hợp (phân biệt đơn vị)
        if bitlaunch_balance > 0 or zingproxy_balance > 0 or cloudfly_balance > 0:
            text += f"💰 **Balance tổng hợp:**\n"
            if bitlaunch_balance > 0:
                text += f"   • BitLaunch: ${bitlaunch_balance:,.2f} USD\n"
            if zingproxy_balance > 0:
                text += f"   • ZingProxy: {zingproxy_balance:,.0f} VND\n"
            if cloudfly_balance > 0:
                text += f"   • CloudFly: ${cloudfly_balance:,.2f} USD\n"
            text += "\n"
        
        # Chi tiết tài khoản thủ công
        if manual_accounts:
            text += f"📝 **Tài khoản thủ công ({len(manual_accounts)}):**\n"
            for acc in manual_accounts:
                text += f"   • **{acc.get('username', acc.get('id', 'Unknown'))}**\n"
                text += f"     - Dịch vụ: {acc.get('service', 'N/A')}\n"
                text += f"     - Ngày hết hạn: {acc.get('expiry', 'N/A')}\n"
                if acc.get('expiry'):
                    try:
                        expiry_date = datetime.strptime(acc['expiry'], '%Y-%m-%d').date()
                        today = datetime.now().date()
                        days_left = (expiry_date - today).days
                        if days_left < 0:
                            text += f"     - Trạng thái: 🚨 Đã hết hạn {abs(days_left)} ngày\n"
                        elif days_left == 0:
                            text += f"     - Trạng thái: 🚨 HẾT HẠN HÔM NAY!\n"
                        elif days_left <= 7:
                            text += f"     - Trạng thái: ⚠️ Còn {days_left} ngày\n"
                        else:
                            text += f"     - Trạng thái: ✅ Còn {days_left} ngày\n"
                    except:
                        text += f"     - Trạng thái: ❓ Không xác định\n"
                text += "\n"
        
        # Chi tiết tài khoản BitLaunch
        if bitlaunch_accounts:
            text += f"🚀 **Tài khoản BitLaunch ({len(bitlaunch_accounts)}):**\n"
            for acc in bitlaunch_accounts:
                balance = acc.get('balance', 0)
                balance_status = "🚨 Balance thấp" if balance < 5 else "✅ Balance ổn"
                text += f"   • **{acc.get('username', acc.get('id', 'Unknown'))}**\n"
                text += f"     - Email: {acc.get('username', 'N/A')}\n"
                text += f"     - Balance: ${balance:,.2f}\n"
                text += f"     - Trạng thái: {balance_status}\n\n"
        
        # Chi tiết tài khoản ZingProxy
        if zingproxy_accounts:
            text += f"🌐 **Tài khoản ZingProxy ({len(zingproxy_accounts)}):**\n"
            for acc in zingproxy_accounts:
                balance = acc.get('balance', 0)
                balance_status = "🚨 Balance thấp" if balance < 100000 else "✅ Balance ổn"
                text += f"   • **{acc.get('username', acc.get('id', 'Unknown'))}**\n"
                text += f"     - Email: {acc.get('username', 'N/A')}\n"
                text += f"     - Balance: {balance:,.0f} VND\n"
                text += f"     - Trạng thái: {balance_status}\n\n"
        
        # Chi tiết tài khoản CloudFly
        if cloudfly_accounts:
            text += f"☁️ **Tài khoản CloudFly ({len(cloudfly_accounts)}):**\n"
            for acc in cloudfly_accounts:
                balance = acc.get('balance', 0)
                balance_status = "🚨 Balance thấp" if balance < 100000 else "✅ Balance ổn"
                text += f"   • **{acc.get('username', acc.get('id', 'Unknown'))}**\n"
                text += f"     - Email: {acc.get('username', 'N/A')}\n"
                text += f"     - Balance: {balance:,.0f} VND\n"
                text += f"     - Trạng thái: {balance_status}\n\n"
        
        # Thống kê cảnh báo
        warnings_count = 0
        expired_count = 0
        low_balance_count = 0
        
        # Đếm tài khoản đã hết hạn
        for acc in manual_accounts:
            if acc.get('expiry'):
                try:
                    expiry_date = datetime.strptime(acc['expiry'], '%Y-%m-%d').date()
                    today = datetime.now().date()
                    days_left = (expiry_date - today).days
                    if days_left <= 0:
                        expired_count += 1
                        warnings_count += 1
                except:
                    pass
        
        # Đếm tài khoản balance thấp
        for acc in accounts:
            if acc.get('source') == 'bitlaunch' and acc.get('balance', 0) < 5:
                low_balance_count += 1
                warnings_count += 1
            elif acc.get('source') == 'zingproxy' and acc.get('balance', 0) < 100000:
                low_balance_count += 1
                warnings_count += 1
            elif acc.get('source') == 'cloudfly' and acc.get('balance', 0) < 100000:
                low_balance_count += 1
                warnings_count += 1
        
        # Tóm tắt cảnh báo
        if warnings_count > 0:
            text += f"⚠️ **Tóm tắt cảnh báo:**\n"
            text += f"   • Tài khoản đã hết hạn: {expired_count}\n"
            text += f"   • Tài khoản balance thấp: {low_balance_count}\n"
            text += f"   • Tổng cảnh báo: {warnings_count}\n\n"
        else:
            text += f"✅ **Không có cảnh báo nào**\n\n"
        
        text += f"🕐 Báo cáo được tạo lúc: {datetime.now().strftime('%H:%M:%S')}"
        
        logger.info(f"[RocketChat] Detailed account info prepared:")
        logger.info(f"[RocketChat] Title: {title}")
        logger.info(f"[RocketChat] Text length: {len(text)} characters")
        logger.info(f"[RocketChat] Warnings: {warnings_count} (expired: {expired_count}, low_balance: {low_balance_count})")
        
        # Chọn màu dựa trên số lượng cảnh báo
        if warnings_count > 0:
            color = "danger" if expired_count > 0 else "warning"
        else:
            color = "good"
        
        logger.info(f"[RocketChat] Selected color: {color}")
        
        # Gửi thông báo
        logger.info(f"[RocketChat] Sending detailed account info to Rocket Chat...")
        result = send_formatted_notification_simple(
            room_id=room_id,
            title=title,
            text=text,
            auth_token=auth_token,
            user_id=user_id,
            color=color
        )
        
        logger.info(f"[RocketChat] send_formatted_notification_simple result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[RocketChat] Error sending detailed account info: {e}")
        import traceback
        logger.error(f"[RocketChat] Traceback: {traceback.format_exc()}")
        return False

def send_daily_account_summary(
    room_id: str,
    auth_token: str,
    user_id: str,
    accounts: List[Dict]
) -> bool:
    """Gửi báo cáo tổng hợp tài khoản hàng ngày"""
    try:
        if not accounts:
            return True
        
        # Thống kê
        total_accounts = len(accounts)
        manual_accounts = len([acc for acc in accounts if acc.get('source') == 'manual'])
        bitlaunch_accounts = len([acc for acc in accounts if acc.get('source') == 'bitlaunch'])
        zingproxy_accounts = len([acc for acc in accounts if acc.get('source') == 'zingproxy'])
        cloudfly_accounts = len([acc for acc in accounts if acc.get('source') == 'cloudfly'])
        
        # Tài khoản sắp hết hạn (chỉ manual)
        today = datetime.now().date()
        expiring_soon = []
        expired_accounts = []  # Thêm danh sách tài khoản đã hết hạn
        
        for account in accounts:
            if account.get('source') == 'manual' and account.get('expiry'):
                try:
                    expiry_date = datetime.strptime(account['expiry'], '%Y-%m-%d').date()
                    days_left = (expiry_date - today).days
                    if days_left < 0:
                        # Tài khoản đã hết hạn
                        expired_accounts.append(account)
                    elif 0 <= days_left <= 7:
                        # Tài khoản sắp hết hạn
                        expiring_soon.append(account)
                except:
                    continue
        
        # Tài khoản có balance thấp
        low_balance_accounts = []
        total_balance = 0
        
        for account in accounts:
            if account.get('source') in ['bitlaunch', 'zingproxy', 'cloudfly']:
                balance = account.get('balance', 0)
                total_balance += balance
                
                # Kiểm tra balance thấp
                if account.get('source') == 'zingproxy':
                    threshold = 100000  # 100,000 VND
                elif account.get('source') == 'bitlaunch':
                    threshold = 5  # $5 USD
                elif account.get('source') == 'cloudfly':
                    threshold = 100000  # 100,000 VND
                else:
                    threshold = 0
                if balance < threshold:
                    low_balance_accounts.append({
                        'account': account,
                        'balance': balance,
                        'threshold': threshold
                    })
        
        # Tạo nội dung báo cáo
        title = f"📊 Báo cáo tài khoản hàng ngày - {datetime.now().strftime('%d/%m/%Y')}"
        
        text = f"**Tổng quan tài khoản:**\n\n"
        text += f"📈 **Tổng số tài khoản:** {total_accounts}\n"
        text += f"   • Thủ công: {manual_accounts}\n"
        text += f"   • BitLaunch: {bitlaunch_accounts}\n"
        text += f"   • ZingProxy: {zingproxy_accounts}\n"
        text += f"   • CloudFly: {cloudfly_accounts}\n\n"
        
        # Thông tin balance tổng hợp
        if bitlaunch_accounts > 0 or zingproxy_accounts > 0 or cloudfly_accounts > 0:
            bitlaunch_balance = sum([acc.get('balance', 0) for acc in accounts if acc.get('source') == 'bitlaunch'])
            zingproxy_balance = sum([acc.get('balance', 0) for acc in accounts if acc.get('source') == 'zingproxy'])
            cloudfly_balance = sum([acc.get('balance', 0) for acc in accounts if acc.get('source') == 'cloudfly'])
            
            text += f"💰 **Balance tổng hợp:**\n"
            if bitlaunch_balance > 0:
                text += f"   • BitLaunch: ${bitlaunch_balance:.2f} USD\n"
            if zingproxy_balance > 0:
                text += f"   • ZingProxy: {zingproxy_balance:,.0f} VND\n"
            if cloudfly_balance > 0:
                text += f"   • CloudFly: {cloudfly_balance:,.0f} VND\n"
            text += "\n"
        
        # Cảnh báo tài khoản sắp hết hạn
        if expiring_soon:
            text += f"⚠️ **Tài khoản sắp hết hạn:** {len(expiring_soon)}\n"
            for account in expiring_soon[:5]:  # Hiển thị 5 tài khoản đầu
                try:
                    expiry_date = datetime.strptime(account['expiry'], '%Y-%m-%d').date()
                    days_left = (expiry_date - today).days
                    text += f"   • {account.get('username', account.get('id'))} - {account.get('service')} (còn {days_left} ngày)\n"
                except:
                    continue
            if len(expiring_soon) > 5:
                text += f"   • ... và {len(expiring_soon) - 5} tài khoản khác\n"
        else:
            text += f"✅ **Không có tài khoản nào sắp hết hạn**\n"
        
        # Cảnh báo tài khoản đã hết hạn
        if expired_accounts:
            text += f"🚨 **Tài khoản đã hết hạn:** {len(expired_accounts)}\n"
            for account in expired_accounts[:5]:  # Hiển thị 5 tài khoản đầu
                try:
                    expiry_date = datetime.strptime(account['expiry'], '%Y-%m-%d').date()
                    days_left = (expiry_date - today).days
                    text += f"   • {account.get('username', account.get('id'))} - {account.get('service')} (đã hết hạn {abs(days_left)} ngày)\n"
                except:
                    continue
            if len(expired_accounts) > 5:
                text += f"   • ... và {len(expired_accounts) - 5} tài khoản khác\n"
        else:
            text += f"✅ **Không có tài khoản nào đã hết hạn**\n"
        
        # Cảnh báo balance thấp
        if low_balance_accounts:
            text += f"💰 **Tài khoản có balance thấp:** {len(low_balance_accounts)}\n"
            for item in low_balance_accounts[:5]:  # Hiển thị 5 tài khoản đầu
                account = item['account']
                balance = item['balance']
                threshold = item['threshold']
                # Format balance dựa trên nguồn
                if account.get('source') in ['zingproxy', 'cloudfly']:
                    balance_str = f"{balance:,.0f} VND"
                    threshold_str = f"{threshold:,.0f} VND"
                else:
                    balance_str = f"${balance:.2f}"
                    threshold_str = f"${threshold}"
                text += f"   • {account.get('username', account.get('id'))} - {account.get('service')} ({balance_str} < {threshold_str})\n"
            if len(low_balance_accounts) > 5:
                text += f"   • ... và {len(low_balance_accounts) - 5} tài khoản khác\n"
        else:
            text += f"✅ **Không có tài khoản nào có balance thấp**\n"
        
        text += f"\n🕐 Báo cáo được tạo lúc: {datetime.now().strftime('%H:%M:%S')}"
        
        return send_formatted_notification_simple(
            room_id=room_id,
            title=title,
            text=text,
            auth_token=auth_token,
            user_id=user_id,
            color="good"
        )
        
    except Exception as e:
        logger.error(f"Error sending daily account summary: {e}")
        return False

# ==================== LEGACY FUNCTIONS ====================

def send_notification_to_rocket_chat(
    room_id: str, 
    message: str, 
    auth_token: str, 
    user_id: str,
    alias: Optional[str] = None
) -> bool:
    """Send notification to Rocket Chat"""
    try:
        client = RocketChatClient(auth_token, user_id)
        result = client.send_message(room_id, message, alias)
        
        if result.get('success'):
            logger.info(f"Rocket Chat notification sent successfully to room {room_id}")
            return True
        else:
            logger.error(f"Rocket Chat API returned error: {result}")
            return False
            
    except RocketChatError as e:
        logger.error(f"Rocket Chat notification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Rocket Chat notification: {e}")
        return False

def send_formatted_notification_to_rocket_chat(
    room_id: str,
    title: str,
    text: str,
    auth_token: str,
    user_id: str,
    color: str = "good"
) -> bool:
    """Send formatted notification to Rocket Chat"""
    try:
        client = RocketChatClient(auth_token, user_id)
        result = client.send_formatted_message(room_id, title, text, color)
        
        if result.get('success'):
            logger.info(f"Rocket Chat formatted notification sent successfully to room {room_id}")
            return True
        else:
            logger.error(f"Rocket Chat API returned error: {result}")
            return False
            
    except RocketChatError as e:
        logger.error(f"Rocket Chat formatted notification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Rocket Chat formatted notification: {e}")
        return False

def get_rocket_chat_channels(auth_token: str, user_id: str) -> List[Dict]:
    """Get list of available channels"""
    try:
        client = RocketChatClient(auth_token, user_id)
        return client.get_channels()
    except Exception as e:
        logger.error(f"Failed to get Rocket Chat channels: {e}")
        return []

def get_rocket_chat_groups(auth_token: str, user_id: str) -> List[Dict]:
    """Get list of available groups"""
    try:
        client = RocketChatClient(auth_token, user_id)
        return client.get_groups()
    except Exception as e:
        logger.error(f"Failed to get Rocket Chat groups: {e}")
        return [] 