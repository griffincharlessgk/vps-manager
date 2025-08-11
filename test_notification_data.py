#!/usr/bin/env python3
"""
Test dữ liệu thông báo tài khoản sắp hết hạn
"""

import os
import sys

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_notification_data():
    """Test dữ liệu được gửi đến notification function"""
    
    print("🧪 Test dữ liệu thông báo tài khoản sắp hết hạn...")
    
    try:
        from ui.app import create_app
        from core.models import db, User
        from core import manager
        
        app = create_app()
        
        with app.app_context():
            # Kiểm tra user admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ Không tìm thấy user admin")
                return
            
            print(f"✅ Tìm thấy user admin: {admin.username} (ID: {admin.id})")
            
            # Lấy dữ liệu tài khoản từ TẤT CẢ nguồn (giống như API endpoint)
            print("\n📊 Lấy dữ liệu tài khoản từ tất cả nguồn...")
            
            # 1. Tài khoản thủ công
            manual_acc_list = manager.list_accounts()
            for acc in manual_acc_list:
                if 'service' not in acc:
                    acc['service'] = ''
                acc['source'] = 'manual'  # Đánh dấu nguồn
            
            print(f"   📝 Manual accounts: {len(manual_acc_list)}")
            for acc in manual_acc_list:
                print(f"      - {acc.get('username', 'N/A')} ({acc.get('service', 'N/A')}) - Expiry: {acc.get('expiry', 'N/A')}")
            
            # 2. Tài khoản từ BitLaunch
            bitlaunch_apis = manager.list_bitlaunch_apis(admin.id)
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
            
            print(f"   🚀 BitLaunch accounts: {len(bitlaunch_acc_list)}")
            for acc in bitlaunch_acc_list:
                print(f"      - {acc.get('username', 'N/A')} - Balance: ${acc.get('balance', 0)}")
            
            # 3. Tài khoản từ ZingProxy
            zingproxy_acc_list = manager.list_zingproxy_accounts(admin.id)
            for acc in zingproxy_acc_list:
                acc['source'] = 'zingproxy'  # Đánh dấu nguồn
                # Map fields để phù hợp với UI
                acc['username'] = acc.get('email', 'N/A')
                acc['service'] = 'ZingProxy'
                acc['expiry'] = None  # ZingProxy không có expiry
                acc['balance'] = acc.get('balance', 0)  # Thêm balance
            
            print(f"   🌐 ZingProxy accounts: {len(zingproxy_acc_list)}")
            for acc in zingproxy_acc_list:
                print(f"      - {acc.get('username', 'N/A')} - Balance: ${acc.get('balance', 0)}")
            
            # 4. Tài khoản từ CloudFly
            cloudfly_apis = manager.list_cloudfly_apis(admin.id)
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
            
            print(f"   ☁️ CloudFly accounts: {len(cloudfly_acc_list)}")
            for acc in cloudfly_acc_list:
                print(f"      - {acc.get('username', 'N/A')} - Balance: ${acc.get('balance', 0)}")
            
            # Kết hợp tất cả tài khoản
            all_accounts = manual_acc_list + bitlaunch_acc_list + zingproxy_acc_list + cloudfly_acc_list
            
            print(f"\n📈 Tổng cộng: {len(all_accounts)} tài khoản")
            print(f"   - Manual: {len(manual_acc_list)}")
            print(f"   - BitLaunch: {len(bitlaunch_acc_list)}")
            print(f"   - ZingProxy: {len(zingproxy_acc_list)}")
            print(f"   - CloudFly: {len(cloudfly_acc_list)}")
            
            # Kiểm tra dữ liệu chi tiết
            print(f"\n🔍 Chi tiết dữ liệu:")
            for i, acc in enumerate(all_accounts[:5]):  # Hiển thị 5 tài khoản đầu
                print(f"   {i+1}. {acc}")
            
            # Test function notification
            print(f"\n🧪 Test function notification...")
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
                accounts=all_accounts,
                warning_days=7
            )
            
            print(f"✅ Kết quả test: {success}")
                
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_notification_data() 