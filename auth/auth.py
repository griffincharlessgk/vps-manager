from flask import Blueprint, request, session, jsonify
from core.models import db, User
from werkzeug.security import check_password_hash
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'msg': 'Sai tài khoản hoặc mật khẩu'}), 401
    session['user_id'] = user.id
    session['role'] = user.role
    return jsonify({'msg': 'Đăng nhập thành công', 'role': user.role})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'msg': 'Đã đăng xuất'})

def require_login():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'msg': 'Bạn cần đăng nhập'}), 401
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def require_admin():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if session.get('role') != 'admin':
                return jsonify({'msg': 'Chỉ admin mới được phép'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator 