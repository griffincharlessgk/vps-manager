#!/usr/bin/env python3
"""
Script khởi tạo database cho VPS Manager
Tạo tất cả bảng và seed dữ liệu admin
"""

import os
import sys

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.app import create_app
from core.models import db, User, VPS, Account, BitLaunchAPI, BitLaunchVPS, ZingProxyAccount, ZingProxy, Proxy, CloudFlyAPI, CloudFlyVPS, RocketChatConfig

def init_database():
    """Khởi tạo database và tạo admin user"""
    print("🚀 Khởi tạo database VPS Manager...")
    
    # Tạo app context
    app = create_app()
    
    with app.app_context():
        try:
            # Tạo tất cả bảng
            print("📋 Tạo các bảng database...")
            db.create_all()
            print("✅ Đã tạo tất cả bảng thành công!")
            
            # Kiểm tra xem đã có admin user chưa
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print("👤 Admin user đã tồn tại")
            else:
                # Tạo admin user
                print("👤 Tạo admin user...")
                admin = User(username='admin', role='admin')
                admin.set_password('123')  # Mật khẩu mặc định: 123
                db.session.add(admin)
                db.session.commit()
                print("✅ Đã tạo admin user thành công!")
                print("   Username: admin")
                print("   Password: 123")
                print("   ⚠️  Vui lòng đổi mật khẩu sau khi đăng nhập!")
            
            # Kiểm tra các bảng đã được tạo
            tables = [
                'users', 'vps', 'accounts', 'bitlaunch_apis', 'bitlaunch_vps',
                'zingproxy_accounts', 'zingproxies', 'proxies', 
                'cloudfly_apis', 'cloudfly_vps', 'rocket_chat_configs'
            ]
            
            print("\n📊 Kiểm tra các bảng đã tạo:")
            for table in tables:
                try:
                    # Thử query để kiểm tra bảng có tồn tại không
                    db.session.execute(f"SELECT COUNT(*) FROM {table}")
                    print(f"   ✅ {table}")
                except Exception as e:
                    print(f"   ❌ {table} - Lỗi: {e}")
            
            print("\n🎉 Khởi tạo database hoàn tất!")
            print("🌐 Bạn có thể chạy ứng dụng bằng lệnh: python -m ui.app")
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo database: {e}")
            return False
    
    return True

if __name__ == '__main__':
    success = init_database()
    if success:
        print("\n✅ Database đã sẵn sàng!")
    else:
        print("\n❌ Có lỗi xảy ra khi khởi tạo database!")
        sys.exit(1) 