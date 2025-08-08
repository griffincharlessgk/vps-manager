#!/usr/bin/env python3
"""
Test script để kiểm tra BitLaunch API integration
"""

from core.api_clients.bitlaunch import BitLaunchClient
import os

def test_bitlaunch_api():
    # Sử dụng API key từ environment hoặc input
    api_key = os.getenv('BITLAUNCH_API_KEY', '')
    
    if not api_key:
        api_key = input("Nhập BitLaunch API key: ")
    
    print(f"🧪 Testing BitLaunch API với key: {api_key[:10]}...")
    
    try:
        client = BitLaunchClient(api_key)
        
        print("\n📋 Testing get_servers...")
        servers = client.get_servers()
        print(f"✅ Servers count: {len(servers)}")
        
        if servers:
            first_server = servers[0]
            print(f"✅ First server keys: {list(first_server.keys())}")
            
            # Test field mapping
            name = first_server.get('name', '')
            ipv4 = first_server.get('ipv4', '')
            region = first_server.get('region', '')
            size_description = first_server.get('sizeDescription', '')
            status = first_server.get('status', '')
            
            print(f"✅ Name: {name}")
            print(f"✅ IPv4: {ipv4}")
            print(f"✅ Region: {region}")
            print(f"✅ Size Description: {size_description}")
            print(f"✅ Status: {status}")
            
            # Test if fields are properly mapped
            if ipv4 and ipv4 != 'N/A':
                print("✅ IP mapping: OK")
            else:
                print("❌ IP mapping: FAILED")
                
            if region and region != 'N/A':
                print("✅ Region mapping: OK")
            else:
                print("❌ Region mapping: FAILED")
                
            if size_description and size_description != 'N/A':
                print("✅ Plan mapping: OK")
            else:
                print("❌ Plan mapping: FAILED")
        
        print(f"\n🎉 BitLaunch API test hoàn thành!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_bitlaunch_api() 