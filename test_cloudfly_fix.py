#!/usr/bin/env python3
"""
Test script để kiểm tra CloudFly integration đã fix
"""

from core.api_clients.cloudfly import CloudFlyClient
import os

def test_cloudfly_fix():
    # Sử dụng token từ environment hoặc input
    token = os.getenv('CLOUDFLY_TOKEN', '3c9acedd9ef7ce14d496dae71ab44a6ba8d87f1c')
    
    if not token or token == 'your_token_here':
        token = input("Nhập CloudFly token: ")
    
    print(f"🧪 Testing CloudFly API với token: {token[:10]}...")
    
    try:
        client = CloudFlyClient(token)
        
        print("\n📋 Testing get_user_info...")
        user_info = client.get_user_info()
        print(f"✅ User Info Response Keys: {list(user_info.keys())}")
        
        # Test balance extraction
        if 'clients' in user_info and len(user_info['clients']) > 0:
            wallet = user_info['clients'][0].get('wallet', {})
            main_balance = wallet.get('main_balance', 0)
            print(f"✅ Balance extraction: ${main_balance}")
        else:
            print("❌ Không tìm thấy balance trong response")
        
        print("\n📋 Testing list_instances...")
        instances = client.list_instances()
        print(f"✅ Instances count: {len(instances)}")
        
        if instances:
            first_instance = instances[0]
            print(f"✅ First instance keys: {list(first_instance.keys())}")
            
            # Test field mapping
            display_name = first_instance.get('display_name', '')
            ip_address = first_instance.get('accessIPv4', '')
            status = first_instance.get('status', '')
            
            print(f"✅ Display Name: {display_name}")
            print(f"✅ IP Address: {ip_address}")
            print(f"✅ Status: {status}")
            
            # Test nested objects
            region = first_instance.get('region', {})
            flavor = first_instance.get('flavor', {})
            image = first_instance.get('image', {})
            
            print(f"✅ Region: {region.get('description') if isinstance(region, dict) else region}")
            print(f"✅ Flavor: {flavor.get('description') if isinstance(flavor, dict) else flavor}")
            print(f"✅ Image: {image.get('name') if isinstance(image, dict) else image}")
        
        print(f"\n🎉 CloudFly API test hoàn thành!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_cloudfly_fix() 