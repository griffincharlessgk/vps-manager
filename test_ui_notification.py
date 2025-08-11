#!/usr/bin/env python3
"""
Test UI notification với session thực
"""

import requests
import json

def test_ui_notification():
    """Test UI notification với session thực"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing UI notification with real session...")
    
    # 1. Đăng nhập để lấy session
    print("\n1️⃣ Đăng nhập...")
    login_data = {
        'username': 'admin',
        'password': '123456'
    }
    
    session = requests.Session()
    
    try:
        # Đăng nhập
        response = session.post(f"{base_url}/login", data=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Đăng nhập thất bại")
            return
        
        print("✅ Đăng nhập thành công")
        
        # 2. Test gửi thông báo tài khoản sắp hết hạn
        print("\n2️⃣ Testing send account notification...")
        notification_data = {"warning_days": 7}
        
        response = session.post(
            f"{base_url}/api/rocket-chat/send-account-notification",
            json=notification_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ Account notification sent successfully!")
            else:
                print(f"❌ Failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 3. Test gửi báo cáo hàng ngày
    print("\n3️⃣ Testing send daily summary...")
    try:
        response = session.post(
            f"{base_url}/api/rocket-chat/send-daily-summary",
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ Daily summary sent successfully!")
            else:
                print(f"❌ Failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ui_notification() 