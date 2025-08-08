#!/usr/bin/env python3
"""
Script để khởi tạo database với tất cả bảng
"""

import os
import sys

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import create_app
from core.models import db, User

def init_database():
    """Khởi tạo database và tạo admin user nếu chưa có"""
    app = create_app()
    
    with app.app_context():
        print("🗄️  Tạo tất cả bảng database...")
        db.create_all()
        print("✅ Đã tạo tất cả bảng thành công!")
        
        # Tạo admin user nếu chưa có
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("👤 Tạo admin user...")
            admin = User(username='admin', role='admin')
            admin.set_password('123')  # Mật khẩu mặc định: 123
            db.session.add(admin)
            db.session.commit()
            print("✅ Đã tạo admin user thành công!")
            print("   Username: admin")
            print("   Password: 123")
        else:
            print("ℹ️  Admin user đã tồn tại")
        
        print("\n🎉 Khởi tạo database hoàn tất!")
        print("🚀 Chạy 'python run_app.py' để khởi động ứng dụng")

if __name__ == '__main__':
    init_database() 