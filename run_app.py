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
    
    # Khởi tạo app với Celery
    app = init_app()
    
    # Chỉ khởi tạo Celery trong tiến trình chính
    is_reloader_child = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    if not is_reloader_child:
        print("🔄 Đang khởi động Celery...")
        from core.celery_app import init_celery
        celery_app = init_celery(app)
        if celery_app:
            print("✅ Celery đã khởi động thành công")
        else:
            print("❌ Celery không thể khởi động")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
