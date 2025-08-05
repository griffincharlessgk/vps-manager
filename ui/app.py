from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from core import manager
import os
from datetime import datetime, timedelta
from core import notifier
from core.scheduler import start_scheduler
from core.models import db, User, VPS, Account
from werkzeug.security import check_password_hash
from core.api_clients.bitlaunch import BitLaunchClient, BitLaunchAPIError
from core.api_clients.zingproxy import ZingProxyClient, ZingProxyAPIError
from core.models import ZingProxyAccount
from dotenv import load_dotenv
from flask_cors import CORS
import logging
from core.validation import (
    validate_vps_data, validate_account_data, validate_bitlaunch_api_data,
    validate_zingproxy_data, validate_username, validate_password,
    ValidationError
)
from core.logging_config import setup_logging, log_security_event, log_api_request

# Load environment variables
load_dotenv()

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
        vps_list = manager.list_vps()
        for vps in vps_list:
            if 'service' not in vps:
                vps['service'] = ''
        return jsonify(vps_list)

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
        acc_list = manager.list_accounts()
        for acc in acc_list:
            if 'service' not in acc:
                acc['service'] = ''
        return jsonify(acc_list)

    @app.route('/api/expiry-warnings')
    def expiry_warnings():
        # Không yêu cầu đăng nhập cho dashboard
        # if 'user_id' not in session:
        #     return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        warnings = []
        
        from sqlalchemy import text
        
        try:
            # Lấy tất cả VPS
            cursor = db.session.execute(text('SELECT id, name, service, ip, expiry FROM vps'))
            vps_list = cursor.fetchall()
            
            for vps in vps_list:
                if vps.expiry:
                    warnings.append(f"VPS '{vps.name or vps.id}' sẽ hết hạn vào {vps.expiry}")
            
            # Lấy tất cả Accounts
            cursor = db.session.execute(text('SELECT id, username, service, expiry FROM accounts'))
            acc_list = cursor.fetchall()
            
            for acc in acc_list:
                if acc.expiry:
                    warnings.append(f"Account '{acc.username or acc.id}' sẽ hết hạn vào {acc.expiry}")
            
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

    @app.route('/api/test-notification', methods=['POST'])
    def test_notification():
        """Test gửi thông báo thông thường"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        user = User.query.get(session['user_id'])
        if not user.telegram_chat_id:
            return {'status': 'error', 'error': 'Chưa cấu hình Chat ID Telegram'}, 400
        
        try:
            from core.telegram_notify import send_telegram_message
            from core import manager
            
            # Lấy dữ liệu test
            vps_list = manager.list_vps()
            acc_list = manager.list_accounts()
            
            # Gửi thông báo test
            message = f"🧪 **TEST THÔNG BÁO**\n\n"
            message += f"👤 **User:** {user.username}\n"
            message += f"📅 **Thời gian:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            message += f"📊 **Dữ liệu hiện tại:**\n"
            message += f"• VPS: {len(vps_list)} máy chủ\n"
            message += f"• Account: {len(acc_list)} tài khoản\n\n"
            message += f"✅ Đây là thông báo test từ VPS Manager!"
            
            token = os.getenv('TELEGRAM_TOKEN')
            if send_telegram_message(token, user.telegram_chat_id, message):
                return {'status': 'success', 'message': 'Đã gửi thông báo test thành công'}
            else:
                return {'status': 'error', 'error': 'Lỗi gửi thông báo'}, 500
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

    @app.route('/api/telegram-chat-id', methods=['GET', 'POST'])
    def telegram_chat_id_setting():
        if not is_authenticated():
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            user = get_current_user()
            if request.method == 'GET':
                return {'status': 'success', 'telegram_chat_id': user.telegram_chat_id or ''}
            
            # POST: cập nhật
            data = request.get_json()
            if not data:
                return {'status': 'error', 'error': 'Invalid JSON data'}, 400
            
            user.telegram_chat_id = data.get('telegram_chat_id', '').strip()
            db.session.commit()
            return {'status': 'success', 'telegram_chat_id': user.telegram_chat_id}
            
        except Exception as e:
            logger.error(f"Error in telegram chat ID setting: {e}")
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
            acc = manager.add_zingproxy_account(
                user_id=session['user_id'],
                email=email,
                access_token=access_token,
                balance=balance,
                created_at=created_dt,
                update_frequency=update_frequency
            )
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

    @app.route('/zingproxy')
    def zingproxy_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('zingproxy.html')

    @app.route('/notifications')
    def notifications_page():
        auth_check = require_auth()
        if auth_check: return auth_check
        return render_template('notifications.html')

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

    @app.route('/api/test-telegram-simple', methods=['POST'])
    def test_telegram_simple():
        """Test gửi message đơn giản qua Telegram"""
        if 'user_id' not in session:
            return {'status': 'error', 'error': 'Chưa đăng nhập'}, 401
        
        try:
            user = User.query.get(session['user_id'])
            if not user:
                return {'status': 'error', 'error': 'User không tồn tại'}, 404
            
            if not user.telegram_chat_id:
                return {'status': 'error', 'error': 'User chưa có Telegram Chat ID'}, 400
            
            # Test gửi message đơn giản
            from core.telegram_notify import send_telegram_message
            message = f"🧪 **TEST SIMPLE MESSAGE**\n\n"
            message += f"👤 **User:** {user.username}\n"
            message += f"📅 **Thời gian:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            message += f"✅ Đây là test message đơn giản!"
            
            token = os.getenv('TELEGRAM_TOKEN')
            logger.info(f"[API] Testing simple telegram message")
            logger.info(f"[API] Token: {token[:10] if token else 'None'}...")
            logger.info(f"[API] Chat ID: {user.telegram_chat_id}")
            logger.info(f"[API] Message length: {len(message)}")
            
            success = send_telegram_message(token, user.telegram_chat_id, message)
            
            if success:
                logger.info(f"[API] Simple telegram test successful")
                return {'status': 'success', 'message': 'Đã gửi test message đơn giản thành công'}
            else:
                logger.error(f"[API] Simple telegram test failed")
                return {'status': 'error', 'error': 'Lỗi gửi test message đơn giản'}, 500
                
        except Exception as e:
            logger.error(f"Error in test telegram simple: {e}")
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

# Khởi động scheduler ngay khi import module
# start_scheduler()  # Comment lại để tránh khởi động trùng lặp

# Khởi động scheduler khi app được tạo
def init_app():
    """Khởi tạo app với scheduler"""
    from core.scheduler import get_scheduler
    scheduler = get_scheduler()  # Đảm bảo scheduler được khởi động
    print(f"[Scheduler] Scheduler started with {len(scheduler.get_jobs())} jobs")
    return app

if __name__ == '__main__':
    app.run(debug=True) 