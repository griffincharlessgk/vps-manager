#!/usr/bin/env python3
"""
Test logic cảnh báo tài khoản đã hết hạn
"""

import os
import sys
from datetime import datetime, timedelta

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_expired_accounts():
    """Test logic cảnh báo tài khoản đã hết hạn"""
    
    print("🧪 Test logic cảnh báo tài khoản đã hết hạn...")
    
    try:
        from ui.app import create_app
        from core.models import db, User, Account
        from core import manager
        
        app = create_app()
        
        with app.app_context():
            # Kiểm tra user admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ Không tìm thấy user admin")
                return
            
            print(f"✅ Tìm thấy user admin: {admin.username} (ID: {admin.id})")
            
            # Tạo tài khoản test với ngày hết hạn khác nhau
            today = datetime.now().date()
            
            test_accounts = [
                {
                    'username': 'expired_1',
                    'service': 'TestService',
                    'expiry': (today - timedelta(days=5)).strftime('%Y-%m-%d'),  # Hết hạn 5 ngày trước
                    'source': 'manual'
                },
                {
                    'username': 'expired_2', 
                    'service': 'TestService',
                    'expiry': (today - timedelta(days=1)).strftime('%Y-%m-%d'),  # Hết hạn 1 ngày trước
                    'source': 'manual'
                },
                {
                    'username': 'expiring_today',
                    'service': 'TestService', 
                    'expiry': today.strftime('%Y-%m-%d'),  # Hết hạn hôm nay
                    'source': 'manual'
                },
                {
                    'username': 'expiring_tomorrow',
                    'service': 'TestService',
                    'expiry': (today + timedelta(days=1)).strftime('%Y-%m-%d'),  # Hết hạn ngày mai
                    'source': 'manual'
                },
                {
                    'username': 'expiring_soon',
                    'service': 'TestService',
                    'expiry': (today + timedelta(days=3)).strftime('%Y-%m-%d'),  # Hết hạn trong 3 ngày
                    'source': 'manual'
                },
                {
                    'username': 'expiring_later',
                    'service': 'TestService',
                    'expiry': (today + timedelta(days=10)).strftime('%Y-%m-%d'),  # Hết hạn trong 10 ngày
                    'source': 'manual'
                }
            ]
            
            print(f"\n📊 Test accounts với ngày hết hạn khác nhau:")
            for acc in test_accounts:
                expiry_date = datetime.strptime(acc['expiry'], '%Y-%m-%d').date()
                days_left = (expiry_date - today).days
                status = "🚨 Đã hết hạn" if days_left < 0 else "⚠️ Sắp hết hạn" if days_left <= 7 else "✅ Còn xa"
                print(f"   • {acc['username']}: {acc['expiry']} (còn {days_left} ngày) - {status}")
            
            # Test function notification với warning_days = 7
            print(f"\n🧪 Test function notification với warning_days = 7...")
            from core.rocket_chat import send_account_expiry_notification
            
            # Giả lập config
            mock_config = type('MockConfig', (), {
                'room_id': 'test_room',
                'auth_token': 'test_token',
                'user_id_rocket': 'test_user'
            })()
            
            success = send_account_expiry_notification(
                room_id=mock_config.room_id,
                auth_token=mock_config.auth_token,
                user_id=mock_config.user_id_rocket,
                accounts=test_accounts,
                warning_days=7
            )
            
            print(f"✅ Kết quả test: {success}")
            
            # Test với warning_days = 0 (chỉ cảnh báo hết hạn hôm nay)
            print(f"\n🧪 Test function notification với warning_days = 0...")
            success = send_account_expiry_notification(
                room_id=mock_config.room_id,
                auth_token=mock_config.auth_token,
                user_id=mock_config.user_id_rocket,
                accounts=test_accounts,
                warning_days=0
            )
            
            print(f"✅ Kết quả test: {success}")
                
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_expired_accounts() 