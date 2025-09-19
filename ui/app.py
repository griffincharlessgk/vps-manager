import sys
import os

# Thêm thư mục gốc vào Python path để có thể import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables TRƯỚC KHI import các core modules
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from core import manager
from datetime import datetime, timedelta
from core import notifier
from core.scheduler import start_scheduler
from core.models import db, User, VPS, Account, CloudFlyAPI
from werkzeug.security import check_password_hash
from core.api_clients.bitlaunch import BitLaunchClient, BitLaunchAPIError
from core.api_clients.zingproxy import ZingProxyClient, ZingProxyAPIError
from core.api_clients.cloudfly import CloudFlyClient, CloudFlyAPIError
from core.models import ZingProxyAccount
from flask_cors import CORS
import logging
from core.validation import (
    validate_vps_data, validate_account_data, validate_bitlaunch_api_data,
    validate_zingproxy_data, validate_username, validate_password,
    ValidationError
)
from core.logging_config import setup_logging, log_security_event, log_api_request
from core.rocket_chat import send_daily_account_summary, send_account_expiry_notification, send_detailed_account_info

# Configure logging
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Security configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/users.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Session configuration for development
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to False for development
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    
    # CORS configuration
    CORS(app, origins=['*'], supports_credentials=True)
    
    db.init_app(app)

    # Setup logging
    setup_logging(app)

    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Access forbidden'}), 403

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(ValidationError)
    def validation_error(error):
        logger.warning(f"Validation error: {error}")
        return jsonify({'error': str(error)}), 400

    # Authentication helper functions
    def is_authenticated():
        """Check if user is authenticated"""
        return 'user_id' in session

    def is_admin():
        """Check if user is admin"""
        return is_authenticated() and session.get('role') == 'admin'

    def require_auth():
        """Decorator to require authentication"""
        if not is_authenticated():
            return redirect(url_for('login_page'))
        return None

    def require_admin_auth():
        """Decorator to require admin authentication"""
        if not is_authenticated():
            return redirect(url_for('login_page'))
        if not is_admin():
            # Redirect về dashboard với thông báo lỗi
            return redirect(url_for('dashboard') + '?error=access_denied')
        return None

    def get_current_user():
        """Get current authenticated user"""
        if is_authenticated():
            return User.query.get(session['user_id'])
        return None

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return jsonify({'msg': 'Đã đăng xuất'})

    @app.route('/me')
    def me():
        user = get_current_user()
        if user:
            return jsonify({'username': user.username, 'role': user.role})
        return jsonify({})

    @app.route('/')
    def dashboard():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('dashboard.html')

    @app.route('/vps')
    def vps_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('vps.html')

    @app.route('/accounts')
    def accounts_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('accounts.html')

    @app.route('/expiry')
    def expiry_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('expiry.html')

    @app.route('/api/vps')
    def list_vps():
        """Lấy danh sách VPS từ tất cả nguồn: manual, BitLaunch, CloudFly"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            # Lấy VPS thủ công
            manual_vps_list = manager.list_vps()
            for vps in manual_vps_list:
                if 'service' not in vps:
                    vps['service'] = ''
                vps['source'] = 'manual'  # Đánh dấu nguồn
            
            # Lấy VPS từ BitLaunch
            bitlaunch_vps_list = manager.list_bitlaunch_vps(session['user_id'])
            for vps in bitlaunch_vps_list:
                vps['source'] = 'bitlaunch'  # Đánh dấu nguồn
                # Map fields để phù hợp với UI
                vps['service'] = 'BitLaunch'
                vps['ip'] = vps.get('ip_address', 'N/A')
                vps['expiry'] = None  # BitLaunch không có expiry
            
            # Lấy VPS từ CloudFly
            cloudfly_vps_list = manager.list_cloudfly_vps(session['user_id'])
            for vps in cloudfly_vps_list:
                vps['source'] = 'cloudfly'  # Đánh dấu nguồn
                # Map fields để phù hợp với UI
                vps['service'] = 'CloudFly'
                vps['ip'] = vps.get('ip_address', 'N/A')
                vps['expiry'] = None  # CloudFly không có expiry
            
            # Kết hợp tất cả VPS
            all_vps = manual_vps_list + bitlaunch_vps_list + cloudfly_vps_list
            
            return jsonify(all_vps)
            
        except Exception as e:
            logger.error(f"Error listing VPS: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/vps', methods=['POST'])
    def add_vps():
        try:
            data = request.json
            validated_data = validate_vps_data(data)
            manager.add_vps(validated_data)
            logger.info(f"VPS added: {validated_data.get('id')}")
            return jsonify({'msg': 'Đã thêm VPS'}), 201
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error adding VPS: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/vps/<vps_id>', methods=['PUT'])
    def update_vps(vps_id):
        data = request.json
        if 'service' not in data:
            data['service'] = ''
        manager.update_vps(vps_id, data)
        return {'status': 'ok'}

    @app.route('/api/vps/<vps_id>', methods=['DELETE'])
    def delete_vps(vps_id):
        manager.delete_vps(vps_id)
        return {'status': 'ok'}

    @app.route('/api/accounts', methods=['POST'])
    def add_account():
        try:
            data = request.json
            validated_data = validate_account_data(data)
            manager.add_account(validated_data)
            logger.info(f"Account added: {validated_data.get('id')}")
            return jsonify({'msg': 'Đã thêm Account'}), 201
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error adding account: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/accounts/<acc_id>', methods=['PUT'])
    def update_account(acc_id):
        data = request.json
        if 'service' not in data:
            data['service'] = ''
        manager.update_account(acc_id, data)
        return {'status': 'ok'}

    @app.route('/api/accounts/<acc_id>', methods=['DELETE'])
    def delete_account(acc_id):
        manager.delete_account(acc_id)
        return {'status': 'ok'}

    @app.route('/api/accounts')
    def list_accounts():
        """Lấy danh sách tài khoản từ tất cả nguồn: manual, BitLaunch, ZingProxy, CloudFly"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            # Lấy tài khoản thủ công
            manual_acc_list = manager.list_accounts()
            for acc in manual_acc_list:
                if 'service' not in acc:
                    acc['service'] = ''
                acc['source'] = 'manual'  # Đánh dấu nguồn
            
            # Lấy tài khoản từ BitLaunch
            bitlaunch_apis = manager.list_bitlaunch_apis(session['user_id'])
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
            
            # Lấy tài khoản từ ZingProxy
            zingproxy_acc_list = manager.list_zingproxy_accounts(session['user_id'])
            for acc in zingproxy_acc_list:
                acc['source'] = 'zingproxy'  # Đánh dấu nguồn
                # Map fields để phù hợp với UI
                acc['username'] = acc.get('email', 'N/A')
                acc['service'] = 'ZingProxy'
                acc['expiry'] = None  # ZingProxy không có expiry
                acc['balance'] = acc.get('balance', 0)  # Thêm balance
            
            # Lấy tài khoản từ CloudFly
            cloudfly_apis = manager.list_cloudfly_apis(session['user_id'])
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
            
            return jsonify(all_accounts)
            
        except Exception as e:
            logger.error(f"Error listing accounts: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    def parse_expiry_date(date_str):
        """Helper function để parse ngày hết hạn từ nhiều định dạng khác nhau"""
        try:
            if not date_str:
                return None
                
            # Xử lý ISO 8601 format: 2025-10-11T03:25:07.000Z
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            # Xử lý YYYY-MM-DD format
            else:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception as e:
            logger.warning(f"Error parsing expiry date {date_str}: {e}")
            return None

    @app.route('/api/expiry-warnings')
    def expiry_warnings():
        """API trả về danh sách cảnh báo hết hạn có cấu trúc"""
        try:
            from sqlalchemy import text
            from datetime import datetime
            
            today = datetime.now().date()
            warning_days = 7
            warnings = []
            
            # Lấy tất cả VPS
            cursor = db.session.execute(text('SELECT id, name, service, ip, expiry FROM vps WHERE expiry IS NOT NULL'))
            vps_list = cursor.fetchall()
            
            for vps in vps_list:
                if vps.expiry:
                    expiry_date = parse_expiry_date(vps.expiry)
                    if expiry_date:
                        days_left = (expiry_date - today).days
                        if days_left <= warning_days:  # Bao gồm cả items đã hết hạn
                            warnings.append({
                                'item_type': 'VPS',
                                'name': vps.name or f"VPS-{vps.id}",
                                'service': vps.service or 'N/A',
                                'ip': vps.ip or 'N/A',
                                'expiry': expiry_date.strftime('%Y-%m-%d'),
                                'days_left': days_left
                            })
            
            # Lấy tất cả Accounts
            cursor = db.session.execute(text('SELECT id, username, service, expiry FROM accounts WHERE expiry IS NOT NULL'))
            acc_list = cursor.fetchall()
            
            for acc in acc_list:
                if acc.expiry:
                    expiry_date = parse_expiry_date(acc.expiry)
                    if expiry_date:
                        days_left = (expiry_date - today).days
                        if days_left <= warning_days:  # Bao gồm cả items đã hết hạn
                            warnings.append({
                                'item_type': 'Account',
                                'name': acc.username or f"Account-{acc.id}",
                                'service': acc.service or 'N/A',
                                'ip': 'N/A',
                                'expiry': expiry_date.strftime('%Y-%m-%d'),
                                'days_left': days_left
                            })
            
            # Lấy tất cả Proxies (nếu user đã đăng nhập)
            if 'user_id' in session:
                # Proxy từ ZingProxy
                cursor = db.session.execute(text('''
                    SELECT zp.proxy_id, zp.ip, zp.type, zp.expire_at, zpa.email 
                    FROM zingproxies zp 
                    JOIN zingproxy_accounts zpa ON zp.account_id = zpa.id 
                    WHERE zpa.user_id = :user_id AND zp.expire_at IS NOT NULL
                '''), {'user_id': session['user_id']})
                proxy_list = cursor.fetchall()
                
                for proxy in proxy_list:
                    if proxy.expire_at:
                        expiry_date = parse_expiry_date(proxy.expire_at)
                        if expiry_date:
                            days_left = (expiry_date - today).days
                            if days_left <= warning_days:  # Bao gồm cả items đã hết hạn
                                warnings.append({
                                    'item_type': 'Proxy',
                                    'name': f"{proxy.proxy_id} ({proxy.type})",
                                    'service': 'ZingProxy',
                                    'ip': proxy.ip,
                                    'expiry': expiry_date.strftime('%Y-%m-%d'),
                                    'days_left': days_left
                                })
                
                # Proxy từ hệ thống quản lý proxy
                cursor = db.session.execute(text('''
                    SELECT name, ip, port, expire_at, source 
                    FROM proxies 
                    WHERE user_id = :user_id AND expire_at IS NOT NULL
                '''), {'user_id': session['user_id']})
                managed_proxy_list = cursor.fetchall()
                
                for proxy in managed_proxy_list:
                    if proxy.expire_at:
                        expiry_date = parse_expiry_date(proxy.expire_at)
                        if expiry_date:
                            days_left = (expiry_date - today).days
                            if days_left <= warning_days:  # Bao gồm cả items đã hết hạn
                                source_text = f"[{proxy.source}]" if proxy.source != 'manual' else ""
                                warnings.append({
                                    'item_type': 'Proxy',
                                    'name': f"{proxy.name} {source_text}",
                                    'service': 'Proxy Management',
                                    'ip': f"{proxy.ip}:{proxy.port}",
                                    'expiry': expiry_date.strftime('%Y-%m-%d'),
                                    'days_left': days_left
                                })
            
            # Sắp xếp theo số ngày còn lại (gần hết hạn trước)
            warnings.sort(key=lambda x: x['days_left'])
            
            return {'status': 'success', 'warnings': warnings}
            
        except Exception as e:
            logger.error(f"Error getting expiry warnings: {e}")
            return {'status': 'error', 'error': 'Lỗi khi lấy cảnh báo hết hạn'}, 500

    @app.route('/api/notify-telegram', methods=['POST'])
    def notify_telegram():
        vps_list = manager.list_vps()
        acc_list = manager.list_accounts()
        notifier.notify_expiry_telegram_per_user(vps_list, item_type='VPS')
        notifier.notify_expiry_telegram_per_user(acc_list, item_type='Account')
        return {'status': 'sent'}

    @app.route('/api/send-all-notifications', methods=['POST'])
    def send_all_notifications():
        """Gửi tất cả cảnh báo hết hạn cho tất cả users"""
        try:
            # Kiểm tra quyền admin
            if not is_admin():
                return {'status': 'error', 'error': 'Chỉ admin được phép gửi tất cả cảnh báo'}, 403
            
            # Lấy danh sách VPS và Accounts
            vps_list = manager.list_vps()
            acc_list = manager.list_accounts()
            
            # Gửi thông báo cho tất cả users có telegram_chat_id
            from core.models import User
            users = User.query.filter(User.telegram_chat_id.isnot(None)).all()
            
            sent_count = 0
            for user in users:
                try:
                    # Gửi thông báo VPS
                    notifier.notify_expiry_telegram_per_user(vps_list, item_type='VPS')
                    # Gửi thông báo Accounts
                    notifier.notify_expiry_telegram_per_user(acc_list, item_type='Account')
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending notification to user {user.username}: {e}")
                    continue
            
            log_security_event('all_notifications_sent', user_id=get_current_user().username, details=f'Sent to {sent_count} users')
            
            return {
                'status': 'success', 
                'message': f'Đã gửi cảnh báo cho {sent_count} users',
                'sent_count': sent_count
            }
            
        except Exception as e:
            logger.error(f"Error sending all notifications: {e}")
            return {'status': 'error', 'error': 'Lỗi khi gửi tất cả cảnh báo'}, 500

    @app.route('/api/send-daily-summary', methods=['POST'])
    def send_daily_summary():
        """Gửi báo cáo tổng hợp cho user hiện tại"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        user = User.query.get(session['user_id'])
        if not user.telegram_chat_id:
            return {'status': 'error', 'error': 'Chưa cấu hình Chat ID Telegram'}, 400
        try:
            notifier.send_daily_summary(user)
            return {'status': 'success', 'message': 'Đã gửi báo cáo tổng hợp'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


    @app.route('/api/notify-days', methods=['GET', 'POST'])
    def notify_days_setting():
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        user = User.query.get(session['user_id'])
        if request.method == 'GET':
            return {'status': 'success', 'notify_days': user.notify_days or 3}
        # POST: cập nhật
        data = request.json
        try:
            days = int(data.get('notify_days', 3))
            user.notify_days = days
            db.session.commit()
            return {'status': 'success', 'notify_days': user.notify_days}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/notify-settings')
    def notify_settings_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('notify_settings.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        # If already authenticated, redirect to dashboard
        if is_authenticated():
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            try:
                data = request.get_json()
                if not data:
                    logger.warning("Login attempt with invalid JSON data")
                    return {'status': 'error', 'error': 'Invalid JSON data'}, 400
                
                username = data.get('username', '').strip()
                password = data.get('password', '').strip()
                
                if not username or not password:
                    logger.warning(f"Login attempt with missing credentials: username={bool(username)}, password={bool(password)}")
                    return {'status': 'error', 'error': 'Thiếu username hoặc password'}, 400
                
                user = User.query.filter_by(username=username).first()
                if not user:
                    log_security_event('login_failed', user_id=username, details=f'IP: {request.remote_addr}, Reason: user_not_found')
                    return {'status': 'error', 'error': 'Username hoặc password không đúng'}, 401
                
                if not user.check_password(password):
                    log_security_event('login_failed', user_id=username, details=f'IP: {request.remote_addr}, Reason: invalid_password')
                    return {'status': 'error', 'error': 'Username hoặc password không đúng'}, 401
                
                # Set session data
                session.permanent = True  # Make session permanent
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                
                log_security_event('login_success', user_id=username, details=f'IP: {request.remote_addr}')
                logger.info(f"User {username} logged in successfully")
                return {'status': 'success', 'message': 'Đăng nhập thành công'}
                
            except Exception as e:
                logger.error(f"Login error: {e}")
                return {'status': 'error', 'error': 'Lỗi hệ thống'}, 500
        
        return render_template('login.html')



    @app.route('/users')
    def users_page():
        auth_check = require_admin_auth()
        if auth_check: return auth_check
        return render_template('users.html')

    @app.route('/api/users', methods=['GET', 'POST'])
    def api_users():
        if not is_admin():
            return {'status': 'error', 'error': 'Chỉ admin được phép thao tác'}, 403
        
        if request.method == 'GET':
            try:
                users = User.query.all()
                return {'status': 'success', 'users': [
                    {'id': u.id, 'username': u.username, 'role': u.role} for u in users
                ]}
            except Exception as e:
                logger.error(f"Error getting users: {e}")
                return {'status': 'error', 'error': 'Lỗi khi lấy danh sách users'}, 500
        
        # POST: tạo user mới
        try:
            data = request.get_json()
            if not data:
                return {'status': 'error', 'error': 'Invalid JSON data'}, 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            role = data.get('role', '').strip()
            
            if not username or not password or not role:
                return {'status': 'error', 'error': 'Thiếu thông tin'}, 400
            
            if User.query.filter_by(username=username).first():
                return {'status': 'error', 'error': 'Username đã tồn tại'}, 400
            
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            log_security_event('user_created', user_id=username, details=f'Created by: {get_current_user().username}')
            return {'status': 'success', 'user': {'id': user.id, 'username': user.username, 'role': user.role}}
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {'status': 'error', 'error': 'Lỗi khi tạo user'}, 500

    @app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
    def api_user_detail(user_id):
        if not is_admin():
            return {'status': 'error', 'error': 'Chỉ admin được phép thao tác'}, 403
        
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'error': 'User không tồn tại'}, 404
            
            if request.method == 'PUT':
                data = request.get_json()
                if not data:
                    return {'status': 'error', 'error': 'Invalid JSON data'}, 400
                
                if data.get('password'):
                    user.set_password(data['password'])
                if data.get('role'):
                    user.role = data['role']
                
                db.session.commit()
                log_security_event('user_updated', user_id=user.username, details=f'Updated by: {get_current_user().username}')
                return {'status': 'success', 'user': {'id': user.id, 'username': user.username, 'role': user.role}}
            
            if request.method == 'DELETE':
                username = user.username
                db.session.delete(user)
                db.session.commit()
                log_security_event('user_deleted', user_id=username, details=f'Deleted by: {get_current_user().username}')
                return {'status': 'success'}
                
        except Exception as e:
            logger.error(f"Error in user detail API: {e}")
            return {'status': 'error', 'error': 'Lỗi hệ thống'}, 500

    @app.route('/api/test-rocketchat-notification', methods=['POST'])
    def test_rocketchat_notification():
        if not is_authenticated():
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            from core.models import RocketChatConfig
            from core.rocket_chat import send_formatted_notification_simple
            
            user = get_current_user()
            config = RocketChatConfig.query.filter_by(user_id=user.id, is_active=True).first()
            
            if not config:
                return {'status': 'error', 'error': 'Chưa cấu hình RocketChat'}, 400
            
            # Gửi thông báo test
            success = send_formatted_notification_simple(
                room_id=config.room_id,
                title="🧪 Test Notification",
                text=f"Đây là thông báo test từ VPS Manager cho user {user.username}",
                auth_token=config.auth_token,
                user_id=config.user_id_rocket,
                color="good"
            )
            
            if success:
                return {'status': 'success', 'message': 'Test notification sent successfully'}
            else:
                return {'status': 'error', 'error': 'Failed to send test notification'}
                
        except Exception as e:
            logger.error(f"Error in test RocketChat notification: {e}")
            return {'status': 'error', 'error': 'Lỗi hệ thống'}, 500

    @app.route('/api/test-rocketchat-daily-summary', methods=['POST'])
    def test_rocketchat_daily_summary():
        if not is_authenticated():
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            from core.models import RocketChatConfig
            from core import notifier
            
            user = get_current_user()
            config = RocketChatConfig.query.filter_by(user_id=user.id, is_active=True).first()
            
            if not config:
                return {'status': 'error', 'error': 'Chưa cấu hình RocketChat'}, 400
            
            # Gửi daily summary test
            notifier.send_daily_summary_rocketchat(user, config)
            
            return {'status': 'success', 'message': 'Test daily summary sent successfully'}
                
        except Exception as e:
            logger.error(f"Error in test RocketChat daily summary: {e}")
            return {'status': 'error', 'error': 'Lỗi hệ thống'}, 500

    @app.route('/bitlaunch')
    def bitlaunch_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('bitlaunch.html')

    @app.route('/api/bitlaunch-account', methods=['POST'])
    def api_bitlaunch_account():
        data = request.json
        token = data.get('token')
        if not token:
            return {'status': 'error', 'error': 'Thiếu API token'}
        try:
            client = BitLaunchClient(token)
            account_info = client.get_account_info()
            return {'status': 'success', 'account': account_info}
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/api/bitlaunch-usage', methods=['POST'])
    def api_bitlaunch_usage():
        data = request.json
        token = data.get('token')
        month = data.get('month')
        if not token:
            return {'status': 'error', 'error': 'Thiếu API token'}
        try:
            client = BitLaunchClient(token)
            usage = client.get_account_usage(month)
            return {'status': 'success', 'usage': usage}
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/api/bitlaunch-history', methods=['POST'])
    def api_bitlaunch_history():
        data = request.json
        token = data.get('token')
        page = data.get('page', 1)
        pPage = data.get('pPage', 25)
        if not token:
            return {'status': 'error', 'error': 'Thiếu API token'}
        try:
            client = BitLaunchClient(token)
            history = client.get_account_history(page, pPage)
            return {'status': 'success', 'history': history}
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/api/bitlaunch-transactions', methods=['POST'])
    def api_bitlaunch_transactions():
        data = request.json
        token = data.get('token')
        page = data.get('page', 1)
        pPage = data.get('pPage', 25)
        if not token:
            return {'status': 'error', 'error': 'Thiếu API token'}
        try:
            client = BitLaunchClient(token)
            transactions = client.list_transactions(page, pPage)
            return {'status': 'success', 'transactions': transactions}
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/api/bitlaunch-create-transaction', methods=['POST'])
    def api_bitlaunch_create_transaction():
        data = request.json
        token = data.get('token')
        amount_usd = data.get('amount_usd')
        crypto_symbol = data.get('crypto_symbol')
        lightning_network = data.get('lightning_network')
        if not token or not amount_usd:
            return {'status': 'error', 'error': 'Thiếu thông tin bắt buộc'}
        try:
            client = BitLaunchClient(token)
            transaction = client.create_transaction(amount_usd, crypto_symbol, lightning_network)
            return {'status': 'success', 'transaction': transaction}
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/api/bitlaunch-servers', methods=['POST'])
    def api_bitlaunch_servers():
        data = request.json
        token = data.get('token')
        if not token:
            return {'status': 'error', 'error': 'Thiếu API token'}
        try:
            client = BitLaunchClient(token)
            servers = client.list_servers()
            return {'status': 'success', 'servers': servers}
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/api/bitlaunch-ssh-keys', methods=['POST'])
    def api_bitlaunch_ssh_keys():
        data = request.json
        token = data.get('token')
        if not token:
            return {'status': 'error', 'error': 'Thiếu API token'}
        try:
            client = BitLaunchClient(token)
            keys = client.list_ssh_keys()
            return {'status': 'success', 'keys': keys}
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/api/bitlaunch-save-api', methods=['POST'])
    def api_bitlaunch_save_api():
        """Lưu API key và lấy thông tin tài khoản"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        data = request.json
        api_key = data.get('api_key')
        update_frequency = data.get('update_frequency', 1)
        
        if not api_key:
            return {'status': 'error', 'error': 'Thiếu API key'}, 400
        
        try:
            # Test API key bằng cách lấy thông tin tài khoản
            client = BitLaunchClient(api_key)
            account_info = client.get_account_info()
            
            if not account_info or 'email' not in account_info:
                return {'status': 'error', 'error': 'API key không hợp lệ hoặc không lấy được thông tin tài khoản'}, 400
            
            email = account_info.get('email')
            balance = account_info.get('balance', 0)
            limit = account_info.get('limit', 0)
            
            # Lưu vào database
            api_obj = manager.add_bitlaunch_api(
                user_id=session['user_id'],
                email=email,
                api_key=api_key,
                update_frequency=update_frequency
            )
            
            # Cập nhật thông tin balance và limit
            manager.update_bitlaunch_info(api_obj.id, balance, limit)
            
            return {
                'status': 'success',
                'message': f'Đã lưu API key cho {email}',
                'account': {
                    'email': email,
                    'balance': balance,
                    'limit': limit
                }
            }
            
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}, 400

    @app.route('/api/bitlaunch-apis')
    def api_bitlaunch_list_apis():
        """Lấy danh sách API keys của user hiện tại"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        apis = manager.list_bitlaunch_apis(session['user_id'])
        return {'status': 'success', 'apis': apis}

    @app.route('/api/bitlaunch-update-info/<int:api_id>', methods=['POST'])
    def api_bitlaunch_update_info(api_id):
        """Cập nhật thông tin tài khoản cho API key cụ thể"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        api_obj = manager.get_bitlaunch_api_by_id(api_id)
        if not api_obj or api_obj.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không tìm thấy API key'}, 404
        
        try:
            client = BitLaunchClient(api_obj.api_key)
            account_info = client.get_account_info()
            
            balance = account_info.get('balance', 0)
            limit = account_info.get('limit', 0)
            
            manager.update_bitlaunch_info(api_id, balance, limit)
            
            return {
                'status': 'success',
                'message': 'Đã cập nhật thông tin tài khoản',
                'account': {
                    'email': api_obj.email,
                    'balance': balance,
                    'limit': limit
                }
            }
            
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}, 400

    @app.route('/api/bitlaunch-delete-api/<int:api_id>', methods=['DELETE'])
    def api_bitlaunch_delete_api(api_id):
        """Xóa API key"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        api_obj = manager.get_bitlaunch_api_by_id(api_id)
        if not api_obj or api_obj.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không tìm thấy API key'}, 404
        
        manager.delete_bitlaunch_api(api_id)
        return {'status': 'success', 'message': 'Đã xóa API key'}

    @app.route('/api/bitlaunch-update-all', methods=['POST'])
    def api_bitlaunch_update_all():
        """Cập nhật thông tin tất cả API keys cần cập nhật"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        apis_to_update = manager.get_bitlaunch_apis_needing_update()
        updated_count = 0
        errors = []
        
        for api in apis_to_update:
            if api.user_id != session['user_id']:
                continue
                
            try:
                client = BitLaunchClient(api.api_key)
                account_info = client.get_account_info()
                
                balance = account_info.get('balance', 0)
                limit = account_info.get('limit', 0)
                
                manager.update_bitlaunch_info(api.id, balance, limit)
                updated_count += 1
                
            except BitLaunchAPIError as e:
                errors.append(f"{api.email}: {str(e)}")
        
        return {
            'status': 'success',
            'message': f'Đã cập nhật {updated_count} tài khoản',
            'updated_count': updated_count,
            'errors': errors
        }

    @app.route('/api/bitlaunch-vps')
    def api_bitlaunch_list_vps():
        """Lấy danh sách VPS của user hiện tại"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        vps_list = manager.list_bitlaunch_vps(session['user_id'])
        return {'status': 'success', 'vps': vps_list}

    @app.route('/api/bitlaunch-update-vps/<int:api_id>', methods=['POST'])
    def api_bitlaunch_update_vps(api_id):
        """Cập nhật danh sách VPS cho API key cụ thể"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        api_obj = manager.get_bitlaunch_api_by_id(api_id)
        if not api_obj or api_obj.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không tìm thấy API key'}, 404
        
        try:
            client = BitLaunchClient(api_obj.api_key)
            servers = client.list_servers()
            
            # Cập nhật danh sách VPS trong database
            manager.update_bitlaunch_vps_list(api_id, servers)
            
            return {
                'status': 'success',
                'message': f'Đã cập nhật {len(servers)} VPS cho {api_obj.email}',
                'servers_count': len(servers)
            }
            
        except BitLaunchAPIError as e:
            return {'status': 'error', 'error': str(e)}, 400

    @app.route('/api/bitlaunch-update-all-vps', methods=['POST'])
    def api_bitlaunch_update_all_vps():
        """Cập nhật VPS cho tất cả API keys của user"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        apis = manager.list_bitlaunch_apis(session['user_id'])
        updated_count = 0
        total_servers = 0
        errors = []
        
        for api in apis:
            api_obj = manager.get_bitlaunch_api_by_id(api['id'])
            if not api_obj:
                continue
                
            try:
                client = BitLaunchClient(api_obj.api_key)
                servers = client.list_servers()
                
                manager.update_bitlaunch_vps_list(api_obj.id, servers)
                updated_count += 1
                total_servers += len(servers)
                
            except BitLaunchAPIError as e:
                errors.append(f"{api_obj.email}: {str(e)}")
        
        return {
            'status': 'success',
            'message': f'Đã cập nhật VPS cho {updated_count} tài khoản, tổng {total_servers} VPS',
            'updated_count': updated_count,
            'total_servers': total_servers,
            'errors': errors
        }

    @app.route('/api/bitlaunch-delete-vps/<int:vps_id>', methods=['DELETE'])
    def api_bitlaunch_delete_vps(vps_id):
        """Xóa VPS"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        vps_obj = manager.get_bitlaunch_vps_by_id(vps_id)
        if not vps_obj:
            return {'status': 'error', 'error': 'Không tìm thấy VPS'}, 404
        
        # Kiểm tra quyền sở hữu
        api_obj = manager.get_bitlaunch_api_by_id(vps_obj.api_id)
        if not api_obj or api_obj.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không có quyền xóa VPS này'}, 403
        
        manager.delete_bitlaunch_vps(vps_id)
        return {'status': 'success', 'message': 'Đã xóa VPS'}

    @app.route('/api/bitlaunch-vps-detail/<int:vps_id>')
    def api_bitlaunch_vps_detail(vps_id):
        """Lấy chi tiết VPS"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        vps_obj = manager.get_bitlaunch_vps_by_id(vps_id)
        if not vps_obj:
            return {'status': 'error', 'error': 'Không tìm thấy VPS'}, 404
        
        # Kiểm tra quyền sở hữu
        api_obj = manager.get_bitlaunch_api_by_id(vps_obj.api_id)
        if not api_obj or api_obj.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không có quyền xem VPS này'}, 403
        
        vps_detail = manager.bitlaunch_vps_to_dict(vps_obj)
        vps_detail['email'] = api_obj.email
        
        return {'status': 'success', 'vps': vps_detail}

    @app.route('/api/zingproxy-login', methods=['POST'])
    def api_zingproxy_login():
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        data = request.json
        access_token = data.get('access_token')
        update_frequency = int(data.get('update_frequency', 1))
        
        if not access_token:
            return {'status': 'error', 'error': 'Thiếu access token'}, 400
        
        try:
            client = ZingProxyClient(access_token=access_token)
            account_info = client.get_account_details()
            balance = account_info.get('balance', 0)
            email = account_info.get('email', 'unknown@zingproxy.com')
            created_at = account_info.get('created_at')
            created_dt = None
            try:
                created_dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S') if created_at else datetime.now()
            except:
                created_dt = datetime.now()
            
            # Kiểm tra xem email đã tồn tại cho user này chưa
            existing_account = ZingProxyAccount.query.filter_by(
                user_id=session['user_id'], 
                email=email
            ).first()
            
            if existing_account:
                return {'status': 'error', 'error': 'Tài khoản với email này đã tồn tại'}, 400
            
            acc = manager.add_zingproxy_account(
                user_id=session['user_id'],
                email=email,
                access_token=access_token,
                balance=balance,
                created_at=created_dt,
                update_frequency=update_frequency
            )
            
            # Tự động cập nhật proxy sau khi thêm tài khoản
            try:
                proxies = client.get_all_active_proxies()
                manager.update_zingproxy_list(acc.id, proxies)
                
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
                        imported_count = manager.import_proxies_from_zingproxy(session['user_id'], zingproxy_data)
                        logger.info(f"Đã tự động import {imported_count} proxy từ ZingProxy vào hệ thống quản lý proxy")
                except Exception as e:
                    logger.warning(f"Không thể import proxy vào hệ thống quản lý: {e}")
                    
            except Exception as e:
                logger.warning(f"Không thể cập nhật proxy cho tài khoản mới: {e}")
            
            return {'status': 'success', 'account': manager.zingproxy_account_to_dict(acc)}
        except ZingProxyAPIError as e:
            return {'status': 'error', 'error': str(e)}, 400

    @app.route('/api/zingproxy-accounts')
    def api_zingproxy_accounts():
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        accs = manager.list_zingproxy_accounts(session['user_id'])
        return {'status': 'success', 'accounts': accs}

    @app.route('/api/zingproxy-update-proxies/<int:acc_id>', methods=['POST'])
    def api_zingproxy_update_proxies(acc_id):
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        acc = ZingProxyAccount.query.get(acc_id)
        if not acc or acc.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không tìm thấy tài khoản'}, 404
        try:
            client = ZingProxyClient(acc.email, '', access_token=acc.access_token)
            proxies = client.get_all_active_proxies()
            manager.update_zingproxy_list(acc_id, proxies)
            return {'status': 'success', 'count': len(proxies)}
        except ZingProxyAPIError as e:
            return {'status': 'error', 'error': str(e)}, 400

    @app.route('/api/zingproxy-proxies/<int:acc_id>')
    def api_zingproxy_proxies(acc_id):
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        acc = ZingProxyAccount.query.get(acc_id)
        if not acc or acc.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không tìm thấy tài khoản'}, 404
        proxies = manager.list_zingproxies(acc_id)
        return {'status': 'success', 'proxies': proxies}

    @app.route('/api/zingproxy-delete-account/<int:acc_id>', methods=['DELETE'])
    def api_zingproxy_delete_account(acc_id):
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        acc = ZingProxyAccount.query.get(acc_id)
        if not acc or acc.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không tìm thấy tài khoản'}, 404
        manager.delete_zingproxy_account(acc_id)
        return {'status': 'success', 'message': 'Đã xóa tài khoản ZingProxy'}

    @app.route('/api/zingproxy-update-account/<int:acc_id>', methods=['POST'])
    def api_zingproxy_update_account(acc_id):
        """Cập nhật thông tin tài khoản ZingProxy"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        acc = ZingProxyAccount.query.get(acc_id)
        if not acc or acc.user_id != session['user_id']:
            return {'status': 'error', 'error': 'Không tìm thấy tài khoản'}, 404
        try:
            client = ZingProxyClient(access_token=acc.access_token)
            account_info = client.get_account_details()
            balance = account_info.get('balance', 0)
            manager.update_zingproxy_account(acc_id, balance)
            return {'status': 'success', 'message': 'Đã cập nhật thông tin tài khoản'}
        except ZingProxyAPIError as e:
            return {'status': 'error', 'error': str(e)}, 400

    @app.route('/api/zingproxy-update-all-accounts', methods=['POST'])
    def api_zingproxy_update_all_accounts():
        """Cập nhật tất cả tài khoản ZingProxy của user"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            accounts = ZingProxyAccount.query.filter_by(user_id=session['user_id']).all()
            updated_count = 0
            for acc in accounts:
                try:
                    client = ZingProxyClient(access_token=acc.access_token)
                    account_info = client.get_account_details()
                    balance = account_info.get('balance', 0)
                    manager.update_zingproxy_account(acc.id, balance)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Lỗi cập nhật tài khoản {acc.id}: {e}")
                    continue
            return {'status': 'success', 'updated_count': updated_count}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/zingproxy-update-all-proxies', methods=['POST'])
    def api_zingproxy_update_all_proxies():
        """Cập nhật proxy cho tất cả tài khoản ZingProxy của user"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            accounts = ZingProxyAccount.query.filter_by(user_id=session['user_id']).all()
            updated_count = 0
            for acc in accounts:
                try:
                    client = ZingProxyClient(access_token=acc.access_token)
                    proxies = client.get_all_active_proxies()
                    manager.update_zingproxy_list(acc.id, proxies)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Lỗi cập nhật proxy cho tài khoản {acc.id}: {e}")
                    continue
            return {'status': 'success', 'updated_count': updated_count}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/zingproxy-statistics')
    def api_zingproxy_statistics():
        """Lấy thống kê ZingProxy cho user"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            accounts = ZingProxyAccount.query.filter_by(user_id=session['user_id']).all()
            total_accounts = len(accounts)
            total_balance = sum(acc.balance or 0 for acc in accounts)
            
            # Đếm tổng số proxy
            total_proxies = 0
            expiring_proxies = 0
            from datetime import datetime, timedelta
            
            for acc in accounts:
                proxies = ZingProxy.query.filter_by(account_id=acc.id).all()
                total_proxies += len(proxies)
                
                # Đếm proxy sắp hết hạn (trong vòng 7 ngày)
                for proxy in proxies:
                    if proxy.expire_at:
                        try:
                            expiry_date = datetime.strptime(proxy.expire_at, '%Y-%m-%d')
                            days_until_expiry = (expiry_date - datetime.now()).days
                            if 0 <= days_until_expiry <= 7:
                                expiring_proxies += 1
                        except:
                            pass
            
            return {
                'status': 'success',
                'total_accounts': total_accounts,
                'total_balance': round(total_balance, 2),
                'total_proxies': total_proxies,
                'expiring_proxies': expiring_proxies
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    # ==================== PROXY MANAGEMENT API ====================

    @app.route('/api/proxies', methods=['GET'])
    def api_proxies_list():
        """Lấy danh sách proxy của user"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            proxies = manager.list_proxies(session['user_id'])
            return {'status': 'success', 'proxies': proxies}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/proxies', methods=['POST'])
    def api_proxies_add():
        """Thêm proxy mới"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            data = request.json
            proxy = manager.add_proxy(session['user_id'], data)
            return {'status': 'success', 'proxy': manager.proxy_to_dict(proxy)}
        except ValueError as e:
            return {'status': 'error', 'error': str(e)}, 400
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/proxies/<int:proxy_id>', methods=['GET'])
    def api_proxies_get(proxy_id):
        """Lấy thông tin proxy"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            proxy = manager.get_proxy_by_id(proxy_id, session['user_id'])
            if not proxy:
                return {'status': 'error', 'error': 'Không tìm thấy proxy'}, 404
            return {'status': 'success', 'proxy': manager.proxy_to_dict(proxy)}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/proxies/<int:proxy_id>', methods=['PUT'])
    def api_proxies_update(proxy_id):
        """Cập nhật proxy"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            data = request.json
            proxy = manager.update_proxy(proxy_id, session['user_id'], data)
            return {'status': 'success', 'proxy': manager.proxy_to_dict(proxy)}
        except ValueError as e:
            return {'status': 'error', 'error': str(e)}, 400
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/proxies/<int:proxy_id>', methods=['DELETE'])
    def api_proxies_delete(proxy_id):
        """Xóa proxy"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            manager.delete_proxy(proxy_id, session['user_id'])
            return {'status': 'success', 'message': 'Đã xóa proxy'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/proxies/statistics')
    def api_proxies_statistics():
        """Lấy thống kê proxy"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            from core.models import Proxy, ZingProxyAccount
            from datetime import datetime
            
            proxies = Proxy.query.filter_by(user_id=session['user_id']).all()
            total_proxies = len(proxies)
            active_proxies = len([p for p in proxies if p.status == 'active'])
            zingproxy_proxies = len([p for p in proxies if p.source == 'zingproxy'])
            
            # Đếm số tài khoản ZingProxy
            zingproxy_accounts = ZingProxyAccount.query.filter_by(user_id=session['user_id']).count()
            
            # Đếm proxy sắp hết hạn (trong vòng 7 ngày)
            expiring_proxies = 0
            for proxy in proxies:
                if proxy.expire_at:
                    try:
                        expiry_date = datetime.strptime(proxy.expire_at, '%Y-%m-%d')
                        days_until_expiry = (expiry_date - datetime.now()).days
                        if 0 <= days_until_expiry <= 7:
                            expiring_proxies += 1
                    except:
                        pass
            
            return {
                'status': 'success',
                'total_proxies': total_proxies,
                'active_proxies': active_proxies,
                'expiring_proxies': expiring_proxies,
                'zingproxy_proxies': zingproxy_proxies,
                'zingproxy_accounts': zingproxy_accounts
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/proxies/import-zingproxy', methods=['POST'])
    def api_proxies_import_zingproxy():
        """Import proxy từ ZingProxy"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            # Lấy tất cả proxy từ ZingProxy
            zingproxy_data = []
            accounts = ZingProxyAccount.query.filter_by(user_id=session['user_id']).all()
            
            for acc in accounts:
                proxies = ZingProxy.query.filter_by(account_id=acc.id).all()
                for proxy in proxies:
                    zingproxy_data.append({
                        'proxy_id': proxy.proxy_id,
                        'ip': proxy.ip,
                        'port': proxy.port,
                        'port_socks5': proxy.port_socks5,
                        'username': proxy.username,
                        'password': proxy.password,
                        'status': proxy.status,
                        'expire_at': proxy.expire_at,
                        'location': proxy.location,
                        'type': proxy.type,
                        'note': proxy.note,
                        'auto_renew': proxy.auto_renew
                    })
            
            if not zingproxy_data:
                return {'status': 'error', 'error': 'Không có proxy nào từ ZingProxy để import'}, 400
            
            imported_count = manager.import_proxies_from_zingproxy(session['user_id'], zingproxy_data)
            return {'status': 'success', 'imported_count': imported_count}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/proxies/export')
    def api_proxies_export():
        """Export danh sách proxy"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            proxies = manager.list_proxies(session['user_id'])
            return {'status': 'success', 'proxies': proxies}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/proxies/sync-zingproxy', methods=['POST'])
    def api_proxies_sync_zingproxy():
        """Đồng bộ proxy từ ZingProxy thủ công"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            from core.api_clients.zingproxy import ZingProxyClient, ZingProxyAPIError
            from core.models import ZingProxyAccount
            
            # Lấy tất cả tài khoản ZingProxy của user
            accounts = ZingProxyAccount.query.filter_by(user_id=session['user_id']).all()
            
            if not accounts:
                return {'status': 'error', 'error': 'Không có tài khoản ZingProxy nào. Vui lòng thêm tài khoản ZingProxy trước.'}, 400
            
            total_proxies_synced = 0
            total_accounts_processed = 0
            failed_accounts = []
            
            logger.info(f"[API] Starting ZingProxy sync for user {session['user_id']} with {len(accounts)} accounts")
            
            for acc in accounts:
                try:
                    logger.info(f"[API] Processing ZingProxy account {acc.id} ({acc.email})")
                    client = ZingProxyClient(access_token=acc.access_token)
                    proxies = client.get_all_active_proxies()
                    
                    logger.info(f"[API] Found {len(proxies)} proxies from account {acc.id}")
                    
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
                    
                    if zingproxy_data:
                        imported_count = manager.import_proxies_from_zingproxy(session['user_id'], zingproxy_data)
                        total_proxies_synced += imported_count
                        total_accounts_processed += 1
                        logger.info(f"[API] Successfully synced {imported_count} proxies from account {acc.id}")
                    else:
                        logger.warning(f"[API] No proxies found for account {acc.id}")
                        
                except ZingProxyAPIError as e:
                    error_msg = f"Lỗi API ZingProxy cho tài khoản {acc.email}: {str(e)}"
                    logger.error(f"[API] {error_msg}")
                    failed_accounts.append({'email': acc.email, 'error': str(e)})
                    continue
                except Exception as e:
                    error_msg = f"Lỗi đồng bộ cho tài khoản {acc.email}: {str(e)}"
                    logger.error(f"[API] {error_msg}")
                    failed_accounts.append({'email': acc.email, 'error': str(e)})
                    continue
            
            # Tạo thông báo kết quả
            result_message = f"Đã đồng bộ {total_proxies_synced} proxy từ {total_accounts_processed}/{len(accounts)} tài khoản"
            if failed_accounts:
                result_message += f". {len(failed_accounts)} tài khoản gặp lỗi."
            
            logger.info(f"[API] ZingProxy sync completed: {result_message}")
            
            return {
                'status': 'success', 
                'total_proxies_synced': total_proxies_synced,
                'total_accounts_processed': total_accounts_processed,
                'total_accounts': len(accounts),
                'failed_accounts': failed_accounts,
                'message': result_message
            }
            
        except Exception as e:
            logger.error(f"[API] Error in ZingProxy sync: {e}")
            return {'status': 'error', 'error': f'Lỗi đồng bộ: {str(e)}'}, 500

    @app.route('/api/proxies/sync-status', methods=['GET'])
    def api_proxies_sync_status():
        """Kiểm tra trạng thái đồng bộ ZingProxy"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        try:
            from core.models import ZingProxyAccount, Proxy
            
            # Lấy thông tin tài khoản ZingProxy
            accounts = ZingProxyAccount.query.filter_by(user_id=session['user_id']).all()
            
            # Lấy thống kê proxy từ ZingProxy
            zingproxy_proxies = Proxy.query.filter_by(
                user_id=session['user_id'], 
                source='zingproxy'
            ).count()
            
            # Lấy thống kê proxy tổng
            total_proxies = Proxy.query.filter_by(user_id=session['user_id']).count()
            
            return {
                'status': 'success',
                'zingproxy_accounts': len(accounts),
                'zingproxy_proxies': zingproxy_proxies,
                'total_proxies': total_proxies,
                'last_sync': None  # TODO: Thêm trường last_sync vào database
            }
            
        except Exception as e:
            logger.error(f"[API] Error getting sync status: {e}")
            return {'status': 'error', 'error': f'Lỗi lấy trạng thái: {str(e)}'}, 500

    @app.route('/zingproxy')
    def zingproxy_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('zingproxy.html')

    @app.route('/proxies')
    def proxies_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('proxies.html')

    @app.route('/notifications')
    def notifications_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('notifications.html')

    @app.route('/cloudfly')
    def cloudfly_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('cloudfly.html')

    @app.route('/api/notify-hour', methods=['GET', 'POST'])
    def notify_hour_setting():
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        user = User.query.get(session['user_id'])
        if not user:
            return {'status': 'error', 'error': 'User không tồn tại'}, 404
        
        if request.method == 'POST':
            data = request.json
            notify_hour = data.get('notify_hour', 8)
            
            if not isinstance(notify_hour, int) or notify_hour < 0 or notify_hour > 23:
                return {'status': 'error', 'error': 'Giờ không hợp lệ (0-23)'}, 400
            
            try:
                user.notify_hour = notify_hour
                db.session.commit()
                return {'status': 'success', 'message': 'Đã cập nhật giờ gửi thông báo'}
            except Exception as e:
                return {'status': 'error', 'error': str(e)}, 500
        
        # GET request
        return {'status': 'success', 'notify_hour': user.notify_hour or 8}

    @app.route('/api/notify-minute', methods=['GET', 'POST'])
    def notify_minute_setting():
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        user = User.query.get(session['user_id'])
        if not user:
            return {'status': 'error', 'error': 'User không tồn tại'}, 404
        
        if request.method == 'POST':
            data = request.json
            notify_minute = data.get('notify_minute', 0)
            
            if not isinstance(notify_minute, int) or notify_minute < 0 or notify_minute > 59:
                return {'status': 'error', 'error': 'Phút không hợp lệ (0-59)'}, 400
            
            try:
                user.notify_minute = notify_minute
                db.session.commit()
                return {'status': 'success', 'message': 'Đã cập nhật phút gửi thông báo'}
            except Exception as e:
                return {'status': 'error', 'error': str(e)}, 500
        
        # GET request
        return {'status': 'success', 'notify_minute': user.notify_minute or 0}

    @app.route('/api/next-notify-countdown')
    def api_next_notify_countdown():
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        user = User.query.get(session['user_id'])
        
        # Lấy giờ và phút gửi thông báo của user
        notify_hour = user.notify_hour if user and user.notify_hour else 8
        notify_minute = user.notify_minute if user and user.notify_minute is not None else 0
        
        # Tính thời điểm gửi notify tiếp theo
        now = datetime.now()
        next_notify_time = now.replace(hour=notify_hour, minute=notify_minute, second=0, microsecond=0)
        if now >= next_notify_time:
            next_notify_time += timedelta(days=1)
        
        seconds_left = int((next_notify_time - now).total_seconds())
        
        # Tính thời gian còn lại
        hours_left = seconds_left // 3600
        minutes_left = (seconds_left % 3600) // 60
        
        # Tạo message
        if hours_left > 0:
            message = f"Thông báo tiếp theo: {hours_left}h {minutes_left}m nữa ({notify_hour:02d}:{notify_minute:02d})"
        else:
            message = f"Thông báo tiếp theo: {minutes_left}m nữa ({notify_hour:02d}:{notify_minute:02d})"
        
        return {
            'status': 'success',
            'message': message,
            'next_notify_in_seconds': seconds_left,
            'next_notify_time': next_notify_time.isoformat(),
            'notify_hour': notify_hour,
            'notify_minute': notify_minute,
            'current_hour': now.hour,
            'current_minute': now.minute
        }

    @app.route('/api/test-daily-summary', methods=['POST'])
    def test_daily_summary():
        """Test gửi daily summary cho user hiện tại"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            user = User.query.get(session['user_id'])
            if not user:
                return {'status': 'error', 'error': 'User không tồn tại'}, 404
            
            logger.info(f"[API] Testing daily summary for user: {user.username}")
            logger.info(f"[API] User telegram_chat_id: {user.telegram_chat_id}")
            logger.info(f"[API] User notify_hour: {user.notify_hour}, notify_minute: {user.notify_minute}")
            
            if not user.telegram_chat_id:
                return {'status': 'error', 'error': 'User chưa có Telegram Chat ID'}, 400
            
            # Gọi function send_daily_summary với force=True để test
            from core.notifier import send_daily_summary
            logger.info(f"[API] Calling send_daily_summary with force=True")
            send_daily_summary(user, force=True)
            
            logger.info(f"[API] Daily summary test completed successfully")
            return {'status': 'success', 'message': 'Đã gửi daily summary test thành công'}
        except Exception as e:
            logger.error(f"Error in test daily summary: {e}")
            return {'status': 'error', 'error': str(e)}, 500


    # CloudFly API Routes
    @app.route('/api/cloudfly/apis', methods=['GET'])
    def api_cloudfly_list_apis():
        """Lấy danh sách CloudFly APIs của user hiện tại"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            apis = manager.list_cloudfly_apis(session['user_id'])
            return apis  # Trả về trực tiếp array thay vì wrap trong object
        except Exception as e:
            logger.error(f"Error listing CloudFly APIs: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/cloudfly/apis', methods=['POST'])
    def api_cloudfly_add_api():
        """Thêm CloudFly API mới"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            data = request.json
            api_token = data.get('api_token')
            update_frequency = data.get('update_frequency', 1)
            
            if not api_token:
                return {'status': 'error', 'error': 'Thiếu API Token'}, 400
            
            # Test API token và lấy thông tin user
            try:
                client = CloudFlyClient(api_token)
                user_info = client.get_user_info()
                
                # Lấy email và main_balance từ API response
                email = user_info.get('email')
                
                # CloudFly API có structure phức tạp: clients[0].wallet.main_balance
                main_balance = 0
                if 'clients' in user_info and len(user_info['clients']) > 0:
                    wallet = user_info['clients'][0].get('wallet', {})
                    main_balance = wallet.get('main_balance', 0)
                
                if not email:
                    return {'status': 'error', 'error': 'Không thể lấy email từ API'}, 400
                
            except CloudFlyAPIError as e:
                return {'status': 'error', 'error': f'API Token không hợp lệ: {str(e)}'}, 400
            
            # Lưu API với email lấy từ API
            api = manager.add_cloudfly_api(session['user_id'], email, api_token, update_frequency)
            
            # Cập nhật thông tin tài khoản với main_balance
            manager.update_cloudfly_info(api.id, main_balance, 0)
            
            return {'status': 'success', 'message': 'Thêm API Token thành công'}
        except ValueError as e:
            return {'status': 'error', 'error': str(e)}, 400
        except Exception as e:
            logger.error(f"Error adding CloudFly API: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/cloudfly/apis/<int:api_id>', methods=['DELETE'])
    def api_cloudfly_delete_api(api_id):
        """Xóa CloudFly API"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            api = manager.get_cloudfly_api_by_id(api_id)
            if not api:
                return {'status': 'error', 'error': 'API không tồn tại'}, 404
            
            if api.user_id != session['user_id']:
                return {'status': 'error', 'error': 'Không có quyền xóa API này'}, 403
            
            manager.delete_cloudfly_api(api_id)
            return {'status': 'success', 'message': 'Xóa API Token thành công'}
        except Exception as e:
            logger.error(f"Error deleting CloudFly API: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/cloudfly/apis/update-all', methods=['POST'])
    def api_cloudfly_update_all_apis():
        """Cập nhật tất cả CloudFly APIs"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            apis = manager.get_cloudfly_apis_needing_update()
            updated_count = 0
            
            for api in apis:
                if api.user_id == session['user_id']:
                    try:
                        client = CloudFlyClient(api.api_token)
                        user_info = client.get_user_info()
                        
                        # CloudFly API có structure phức tạp: clients[0].wallet.main_balance
                        main_balance = 0
                        if 'clients' in user_info and len(user_info['clients']) > 0:
                            wallet = user_info['clients'][0].get('wallet', {})
                            main_balance = wallet.get('main_balance', 0)
                        
                        # CloudFly API không có account_limit, đặt = 0
                        manager.update_cloudfly_info(api.id, main_balance, 0)
                        updated_count += 1
                    except Exception as e:
                        logger.error(f"Error updating CloudFly API {api.id}: {e}")
                        continue
            
            return {'status': 'success', 'message': f'Đã cập nhật {updated_count} API Tokens'}
        except Exception as e:
            logger.error(f"Error updating CloudFly APIs: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/cloudfly/vps', methods=['GET'])
    def api_cloudfly_list_vps():
        """Lấy danh sách VPS CloudFly của user hiện tại"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            vps_list = manager.list_cloudfly_vps(session['user_id'])
            return vps_list  # Trả về trực tiếp array thay vì wrap trong object
        except Exception as e:
            logger.error(f"Error listing CloudFly VPS: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/cloudfly/vps/<int:vps_id>', methods=['GET'])
    def api_cloudfly_vps_detail(vps_id):
        """Lấy chi tiết VPS CloudFly"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            vps = manager.get_cloudfly_vps_by_id(vps_id)
            if not vps:
                return {'status': 'error', 'error': 'VPS không tồn tại'}, 404
            
            # Kiểm tra quyền truy cập
            api = manager.get_cloudfly_api_by_id(vps.api_id)
            if api.user_id != session['user_id']:
                return {'status': 'error', 'error': 'Không có quyền truy cập VPS này'}, 403
            
            vps_dict = manager.cloudfly_vps_to_dict(vps)
            return vps_dict  # Trả về trực tiếp dict thay vì wrap trong object
        except Exception as e:
            logger.error(f"Error getting CloudFly VPS detail: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/cloudfly/vps/<int:vps_id>', methods=['DELETE'])
    def api_cloudfly_delete_vps(vps_id):
        """Xóa VPS CloudFly khỏi hệ thống quản lý"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            vps = manager.get_cloudfly_vps_by_id(vps_id)
            if not vps:
                return {'status': 'error', 'error': 'VPS không tồn tại'}, 404
            
            # Kiểm tra quyền truy cập
            api = manager.get_cloudfly_api_by_id(vps.api_id)
            if api.user_id != session['user_id']:
                return {'status': 'error', 'error': 'Không có quyền xóa VPS này'}, 403
            
            manager.delete_cloudfly_vps(vps_id)
            return {'status': 'success', 'message': 'Xóa VPS thành công'}
        except Exception as e:
            logger.error(f"Error deleting CloudFly VPS: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/cloudfly/vps/update-all', methods=['POST'])
    def api_cloudfly_update_all_vps():
        """Cập nhật tất cả VPS CloudFly"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            apis = manager.list_cloudfly_apis(session['user_id'])
            updated_count = 0
            
            for api_dict in apis:
                api = manager.get_cloudfly_api_by_id(api_dict['id'])
                try:
                    client = CloudFlyClient(api.api_token)
                    instances = client.list_instances()
                    manager.update_cloudfly_vps_list(api.id, instances)
                    updated_count += len(instances)
                except Exception as e:
                    logger.error(f"Error updating CloudFly VPS for API {api.id}: {e}")
                    continue
            
            return {'status': 'success', 'message': f'Đã cập nhật {updated_count} VPS instances'}
        except Exception as e:
            logger.error(f"Error updating CloudFly VPS: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/rocket-chat/config', methods=['GET', 'POST'])
    def api_rocket_chat_config():
        """Quản lý cấu hình Rocket Chat"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        if request.method == 'GET':
            try:
                logger.info(f"[API] Getting Rocket Chat config for user {session['user_id']}")
                config = manager.get_rocket_chat_config(session['user_id'])
                if config:
                    logger.info(f"[API] Found config: id={config.id}, room_id={config.room_id}")
                    config_dict = manager.rocket_chat_config_to_dict(config)
                    logger.info(f"[API] Config dict keys: {list(config_dict.keys())}")
                    logger.info(f"[API] Auth token present: {'auth_token' in config_dict}")
                    return config_dict
                else:
                    logger.info(f"[API] No config found for user {session['user_id']}")
                    return {'status': 'not_found'}
            except Exception as e:
                logger.error(f"Error getting Rocket Chat config: {e}")
                return {'status': 'error', 'error': str(e)}, 500
        
        elif request.method == 'POST':
            try:
                data = request.json
                auth_token = data.get('auth_token')
                user_id_rocket = data.get('user_id_rocket')
                room_id = data.get('room_id')
                room_name = data.get('room_name')
                
                if not all([auth_token, user_id_rocket, room_id]):
                    return {'status': 'error', 'error': 'Thiếu thông tin bắt buộc'}, 400
                
                # Kiểm tra xem đã có config chưa
                existing_config = manager.get_rocket_chat_config(session['user_id'])
                if existing_config:
                    # Cập nhật config hiện có
                    config = manager.update_rocket_chat_config(
                        existing_config.id,
                        auth_token=auth_token,
                        user_id_rocket=user_id_rocket,
                        room_id=room_id,
                        room_name=room_name
                    )
                    return {'status': 'success', 'message': 'Cập nhật cấu hình Rocket Chat thành công'}
                else:
                    # Tạo config mới
                    config = manager.add_rocket_chat_config(
                        session['user_id'],
                        auth_token,
                        user_id_rocket,
                        room_id,
                        room_name
                    )
                    return {'status': 'success', 'message': 'Thêm cấu hình Rocket Chat thành công'}
                    
            except ValueError as e:
                return {'status': 'error', 'error': str(e)}, 400
            except Exception as e:
                logger.error(f"Error managing Rocket Chat config: {e}")
                return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/rocket-chat/channels', methods=['GET'])
    def api_rocket_chat_channels():
        """Lấy danh sách channels từ Rocket Chat"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            data = request.args
            auth_token = data.get('auth_token')
            user_id_rocket = data.get('user_id_rocket')
            
            if not auth_token or not user_id_rocket:
                return {'status': 'error', 'error': 'Thiếu auth_token hoặc user_id_rocket'}, 400
            
            from core.rocket_chat import get_rocket_chat_channels, get_rocket_chat_groups
            
            channels = get_rocket_chat_channels(auth_token, user_id_rocket)
            groups = get_rocket_chat_groups(auth_token, user_id_rocket)
            
            return {
                'status': 'success',
                'channels': channels,
                'groups': groups
            }
            
        except Exception as e:
            logger.error(f"Error getting Rocket Chat channels: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/rocket-chat/send-notification', methods=['POST'])
    def api_rocket_chat_send_notification():
        """Gửi thông báo đến Rocket Chat"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            data = request.json
            message = data.get('message')
            title = data.get('title')
            text = data.get('text')
            color = data.get('color', 'good')
            
            if not message and not (title and text):
                return {'status': 'error', 'error': 'Thiếu nội dung thông báo'}, 400
            
            # Lấy cấu hình Rocket Chat của user
            config = manager.get_rocket_chat_config(session['user_id'])
            if not config:
                return {'status': 'error', 'error': 'Chưa cấu hình Rocket Chat'}, 400
            
            # Sử dụng client đơn giản để tránh lỗi encryption
            from core.rocket_chat import send_formatted_notification_simple
            
            success = False
            if title and text:
                success = send_formatted_notification_simple(
                    config.room_id,
                    title,
                    text,
                    config.auth_token,
                    config.user_id_rocket,
                    color
                )
            else:
                success = send_formatted_notification_simple(
                    config.room_id,
                    "Thông báo từ VPS Manager",
                    message,
                    config.auth_token,
                    config.user_id_rocket,
                    "info"
                )
            
            if success:
                return {'status': 'success', 'message': 'Gửi thông báo thành công'}
            else:
                return {'status': 'error', 'error': 'Gửi thông báo thất bại'}, 500
                
        except Exception as e:
            logger.error(f"Error sending Rocket Chat notification: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/rocket-chat/test', methods=['POST'])
    def api_rocket_chat_test():
        """Test kết nối Rocket Chat"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            data = request.json
            auth_token = data.get('auth_token')
            user_id_rocket = data.get('user_id_rocket')
            room_id = data.get('room_id')
            
            if not all([auth_token, user_id_rocket, room_id]):
                return {'status': 'error', 'error': 'Thiếu thông tin bắt buộc'}, 400
            
            from core.rocket_chat import send_notification_to_rocket_chat
            
            test_message = f"🧪 Test notification từ VPS Manager - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            success = send_notification_to_rocket_chat(
                room_id,
                test_message,
                auth_token,  # Sử dụng trực tiếp
                user_id_rocket,
                alias="VPS Manager Test"
            )
            
            if success:
                return {'status': 'success', 'message': 'Test kết nối thành công! Thông báo đã được gửi.'}
            else:
                return {'status': 'error', 'error': 'Test kết nối thất bại'}, 500
                
        except Exception as e:
            logger.error(f"Error testing Rocket Chat connection: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/rocket-chat')
    def rocket_chat_page():
        """Trang cấu hình Rocket Chat"""
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('rocket_chat.html')

    @app.route('/api/rocket-chat/send-account-notification', methods=['POST'])
    def api_rocket_chat_send_account_notification():
        """Gửi thông báo tài khoản sắp hết hạn đến Rocket Chat"""
        if 'user_id' not in session:
            logger.error(f"[API] User not logged in for account notification")
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            data = request.json
            warning_days = data.get('warning_days', 7)
            
            logger.info(f"[API] Sending account notification for user {session['user_id']}, warning_days: {warning_days}")
            logger.info(f"[API] Request data: {data}")
            
            # Lấy cấu hình Rocket Chat của user
            config = manager.get_rocket_chat_config(session['user_id'])
            if not config:
                logger.error(f"[API] No Rocket Chat config found for user {session['user_id']}")
                return {'status': 'error', 'error': 'Chưa cấu hình Rocket Chat'}, 400
            
            logger.info(f"[API] Found Rocket Chat config: id={config.id}, room_id={config.room_id}, user_id_rocket={config.user_id_rocket}")
            logger.info(f"[API] Auth token present: {bool(config.auth_token)}")
            
            # Lấy danh sách tài khoản từ TẤT CẢ nguồn (giống như accounts page)
            # 1. Tài khoản thủ công
            manual_acc_list = manager.list_accounts()
            for acc in manual_acc_list:
                if 'service' not in acc:
                    acc['service'] = ''
                acc['source'] = 'manual'  # Đánh dấu nguồn
            
            # 2. Tài khoản từ BitLaunch
            bitlaunch_apis = manager.list_bitlaunch_apis(session['user_id'])
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
            zingproxy_acc_list = manager.list_zingproxy_accounts(session['user_id'])
            for acc in zingproxy_acc_list:
                acc['source'] = 'zingproxy'  # Đánh dấu nguồn
                # Map fields để phù hợp với UI
                acc['username'] = acc.get('email', 'N/A')
                acc['service'] = 'ZingProxy'
                acc['expiry'] = None  # ZingProxy không có expiry
                acc['balance'] = acc.get('balance', 0)  # Thêm balance
            
            # 4. Tài khoản từ CloudFly
            cloudfly_apis = manager.list_cloudfly_apis(session['user_id'])
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
            
            logger.info(f"[API] Found {len(all_accounts)} total accounts:")
            logger.info(f"[API]   - Manual: {len(manual_acc_list)}")
            logger.info(f"[API]   - BitLaunch: {len(bitlaunch_acc_list)}")
            logger.info(f"[API]   - ZingProxy: {len(zingproxy_acc_list)}")
            logger.info(f"[API]   - CloudFly: {len(cloudfly_acc_list)}")
            
            if all_accounts:
                for i, acc in enumerate(all_accounts[:3]):
                    logger.info(f"[API] Account {i+1}: {acc.get('username')} ({acc.get('service')}) - Source: {acc.get('source')} - Expiry: {acc.get('expiry')}")
            
            # Gửi thông báo
            from core.rocket_chat import send_account_expiry_notification
            
            logger.info(f"[API] Calling send_account_expiry_notification...")
            success = send_account_expiry_notification(
                room_id=config.room_id,
                auth_token=config.auth_token,  # Sử dụng trực tiếp
                user_id=config.user_id_rocket,
                accounts=all_accounts,  # Sử dụng danh sách đầy đủ
                warning_days=warning_days
            )
            
            logger.info(f"[API] send_account_expiry_notification result: {success}")
            
            if success:
                logger.info(f"[API] Account notification sent successfully")
                return {'status': 'success', 'message': 'Đã gửi thông báo tài khoản sắp hết hạn'}
            else:
                logger.error(f"[API] Account notification failed")
                return {'status': 'error', 'error': 'Gửi thông báo thất bại'}, 500
                
        except Exception as e:
            logger.error(f"Error sending account notification: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/rocket-chat/send-daily-summary', methods=['POST'])
    def api_rocket_chat_send_daily_summary():
        """API gửi báo cáo tổng hợp tài khoản hàng ngày"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            # Lấy config Rocket Chat
            config = manager.get_rocket_chat_config(session['user_id'])
            if not config:
                return {'status': 'error', 'error': 'Chưa cấu hình Rocket Chat'}, 400
            
            # Lấy danh sách tài khoản từ TẤT CẢ nguồn (giống như accounts page)
            manual_acc_list = manager.list_accounts()
            for acc in manual_acc_list:
                if 'service' not in acc: acc['service'] = ''
                acc['source'] = 'manual'
            bitlaunch_apis = manager.list_bitlaunch_apis(session['user_id'])
            bitlaunch_acc_list = []
            for api in bitlaunch_apis:
                acc = {
                    'id': f"bitlaunch_{api['id']}", 'username': api['email'], 'service': 'BitLaunch',
                    'expiry': None, 'balance': api.get('balance', 0), 'source': 'bitlaunch'
                }
                bitlaunch_acc_list.append(acc)
            zingproxy_acc_list = manager.list_zingproxy_accounts(session['user_id'])
            for acc in zingproxy_acc_list:
                acc['source'] = 'zingproxy'
                acc['username'] = acc.get('email', 'N/A')
                acc['service'] = 'ZingProxy'
                acc['expiry'] = None
                acc['balance'] = acc.get('balance', 0) # Added this line
            cloudfly_apis = manager.list_cloudfly_apis(session['user_id'])
            cloudfly_acc_list = []
            for api in cloudfly_apis:
                acc = {
                    'id': f"cloudfly_{api['id']}", 'username': api['email'], 'service': 'CloudFly',
                    'expiry': None, 'balance': api.get('balance', 0), 'source': 'cloudfly'
                }
                cloudfly_acc_list.append(acc)
            all_accounts = manual_acc_list + bitlaunch_acc_list + zingproxy_acc_list + cloudfly_acc_list
            logger.info(f"[API] Found {len(all_accounts)} total accounts:")
            logger.info(f"[API]   - Manual: {len(manual_acc_list)}")
            logger.info(f"[API]   - BitLaunch: {len(bitlaunch_acc_list)}")
            logger.info(f"[API]   - ZingProxy: {len(zingproxy_acc_list)}")
            logger.info(f"[API]   - CloudFly: {len(cloudfly_acc_list)}")
            
            # Gửi báo cáo tổng hợp
            success = send_daily_account_summary(
                room_id=config.room_id, auth_token=config.auth_token, user_id=config.user_id_rocket,
                accounts=all_accounts
            )
            
            if success:
                return {'status': 'success', 'message': 'Đã gửi báo cáo tổng hợp hàng ngày thành công!'}
            else:
                return {'status': 'error', 'error': 'Gửi báo cáo thất bại'}
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return {'status': 'error', 'error': f'Lỗi hệ thống: {str(e)}'}

    @app.route('/api/rocket-chat/send-detailed-info', methods=['POST'])
    def api_rocket_chat_send_detailed_info():
        """API gửi thông tin chi tiết tất cả tài khoản"""
        logger.info(f"[API] send-detailed-info called by user {session.get('user_id', 'unknown')}")
        
        if 'user_id' not in session:
            logger.warning(f"[API] send-detailed-info: User not logged in")
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            logger.info(f"[API] send-detailed-info: Processing for user {session['user_id']}")
            
            # Lấy config Rocket Chat
            config = manager.get_rocket_chat_config(session['user_id'])
            if not config:
                logger.error(f"[API] send-detailed-info: No Rocket Chat config found for user {session['user_id']}")
                return {'status': 'error', 'error': 'Chưa cấu hình Rocket Chat'}, 400
            
            logger.info(f"[API] send-detailed-info: Found config {config.id} for user {session['user_id']}")
            
            # Lấy danh sách tài khoản từ TẤT CẢ nguồn (giống như accounts page)
            manual_acc_list = manager.list_accounts()
            for acc in manual_acc_list:
                if 'service' not in acc: acc['service'] = ''
                acc['source'] = 'manual'
            bitlaunch_apis = manager.list_bitlaunch_apis(session['user_id'])
            bitlaunch_acc_list = []
            for api in bitlaunch_apis:
                acc = {
                    'id': f"bitlaunch_{api['id']}", 'username': api['email'], 'service': 'BitLaunch',
                    'expiry': None, 'balance': api.get('balance', 0), 'source': 'bitlaunch'
                }
                bitlaunch_acc_list.append(acc)
            zingproxy_acc_list = manager.list_zingproxy_accounts(session['user_id'])
            for acc in zingproxy_acc_list:
                acc['source'] = 'zingproxy'
                acc['username'] = acc.get('email', 'N/A')
                acc['service'] = 'ZingProxy'
                acc['expiry'] = None
                acc['balance'] = acc.get('balance', 0)
            cloudfly_apis = manager.list_cloudfly_apis(session['user_id'])
            cloudfly_acc_list = []
            for api in cloudfly_apis:
                acc = {
                    'id': f"cloudfly_{api['id']}", 'username': api['email'], 'service': 'CloudFly',
                    'expiry': None, 'balance': api.get('balance', 0), 'source': 'cloudfly'
                }
                cloudfly_acc_list.append(acc)
            all_accounts = manual_acc_list + bitlaunch_acc_list + zingproxy_acc_list + cloudfly_acc_list
            logger.info(f"[API] send-detailed-info: Found {len(all_accounts)} total accounts for user {session['user_id']}:")
            logger.info(f"[API]   - Manual: {len(manual_acc_list)}")
            logger.info(f"[API]   - BitLaunch: {len(bitlaunch_acc_list)}")
            logger.info(f"[API]   - ZingProxy: {len(zingproxy_acc_list)}")
            logger.info(f"[API]   - CloudFly: {len(cloudfly_acc_list)}")
            
            # Gửi thông tin chi tiết
            logger.info(f"[API] send-detailed-info: Calling send_detailed_account_info...")
            success = send_detailed_account_info(
                room_id=config.room_id, auth_token=config.auth_token, user_id=config.user_id_rocket,
                accounts=all_accounts
            )
            
            logger.info(f"[API] send-detailed-info: send_detailed_account_info result: {success}")
            
            if success:
                logger.info(f"[API] send-detailed-info: Success for user {session['user_id']}")
                return {'status': 'success', 'message': 'Đã gửi thông tin chi tiết tài khoản thành công!'}
            else:
                logger.error(f"[API] send-detailed-info: Failed for user {session['user_id']}")
                return {'status': 'error', 'error': 'Gửi thông tin chi tiết thất bại'}
            
        except Exception as e:
            logger.error(f"[API] send-detailed-info: Error for user {session.get('user_id', 'unknown')}: {e}")
            import traceback
            logger.error(f"[API] send-detailed-info: Traceback: {traceback.format_exc()}")
            return {'status': 'error', 'error': f'Lỗi hệ thống: {str(e)}'}

    @app.route('/api/scheduler/status')
    def api_scheduler_status():
        """Kiểm tra trạng thái scheduler"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            from core.scheduler import get_scheduler_status
            scheduler_status = get_scheduler_status()
            return scheduler_status
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    @app.route('/api/scheduler/restart', methods=['POST'])
    def api_scheduler_restart():
        """Khởi động lại scheduler (chỉ admin)"""
        if not is_admin():
            return {'status': 'error', 'error': 'Chỉ admin được phép khởi động lại scheduler'}, 403
        
        try:
            from core.scheduler import get_scheduler
            scheduler = get_scheduler()
            
            if scheduler.running:
                scheduler.shutdown()
                logger.info("[API] Scheduler shutdown")
            
            # Khởi động lại
            from core.scheduler import start_scheduler
            new_scheduler = start_scheduler()
            
            return {
                'status': 'success',
                'message': 'Scheduler đã được khởi động lại',
                'jobs_count': len(new_scheduler.get_jobs())
            }
        except Exception as e:
            logger.error(f"Error restarting scheduler: {e}")
            return {'status': 'error', 'error': str(e)}, 500

    return app

app = create_app()

# Tạm thời comment để tránh lỗi database
# with app.app_context():
#     db.create_all()  # Đảm bảo luôn tạo schema mới trước khi truy vấn User
#     # Seed user admin nếu chưa có
#     if not User.query.filter_by(username='admin').first():
#         admin = User(username='admin', role='admin')
#         admin.set_password('123')  # Đặt mật khẩu admin là 123
#         db.session.add(admin)
#         db.session.commit()

# Khởi động scheduler khi app được tạo
def init_app():
    """Khởi tạo app với scheduler"""
    try:
        from core.scheduler import get_scheduler
        print("🔄 Đang khởi động scheduler...")
        
        # Khởi động scheduler
        scheduler = get_scheduler()
        
        # Kiểm tra trạng thái scheduler
        if scheduler.running:
            print(f"✅ Scheduler đã khởi động thành công với {len(scheduler.get_jobs())} jobs")
            
            # In danh sách jobs
            print("📋 Danh sách jobs đang chạy:")
            for job in scheduler.get_jobs():
                print(f"   • {job.id}: {job.trigger}")
        else:
            print("❌ Scheduler không thể khởi động")
            
        return app
        
    except Exception as e:
        print(f"❌ Lỗi khởi động scheduler: {e}")
        import traceback
        traceback.print_exc()
        return app

if __name__ == '__main__':
    app.run(debug=True) 