#!/usr/bin/env python3
"""
Script để chạy Flask application
"""

import os
import sys

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import create_app, init_app

if __name__ == '__main__':
    print("🚀 Khởi động VPS Manager...")
    print("📱 Truy cập: http://localhost:5000")
    print("⏹️  Dừng: Ctrl+C")
    print("-" * 50)
    
    # Khởi tạo app với scheduler
    app = init_app()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
