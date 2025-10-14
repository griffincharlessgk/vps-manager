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

    # Tạo app trước
    app = create_app()

    # Chỉ khởi động scheduler trong tiến trình chính của reloader
    # Tránh việc scheduler chạy 2 lần khi debug reloader spawn process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or os.environ.get('RUN_MAIN') == 'true':
        init_app()

    # Bật reloader nhưng scheduler chỉ chạy 1 lần nhờ guard ở trên
    app.run(debug=True, host='0.0.0.0', port=5000)
