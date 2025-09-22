#!/bin/bash

# VPS Manager Cron Job Installation Script
# Script để cài đặt và cấu hình cron jobs thay thế cho scheduler

set -e

echo "🚀 VPS Manager Cron Job Installation"
echo "====================================="

# Kiểm tra quyền root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Không nên chạy script này với quyền root"
    echo "   Hãy chạy với user thường: ./install_cron.sh"
    exit 1
fi

# Tạo thư mục logs nếu chưa có
echo "📁 Tạo thư mục logs..."
mkdir -p /home/ubuntu/vps-manager/logs

# Cấp quyền thực thi cho script
echo "🔐 Cấp quyền thực thi cho cron_job.sh..."
chmod +x /home/ubuntu/vps-manager/scripts/cron_job.sh

# Tạo log file nếu chưa có
echo "📝 Tạo log file..."
touch /home/ubuntu/vps-manager/logs/cron_job.log

# Kiểm tra VPS Manager server có chạy không
echo "🔍 Kiểm tra VPS Manager server..."
if curl -s http://localhost:5000/me > /dev/null 2>&1; then
    echo "✅ VPS Manager server đang chạy"
else
    echo "⚠️  VPS Manager server không chạy tại http://localhost:5000"
    echo "   Hãy khởi động server trước khi cài đặt cron jobs"
    read -p "Bạn có muốn tiếp tục không? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Test script
echo "🧪 Test cron job script..."
if /home/ubuntu/vps-manager/scripts/cron_job.sh notifications > /dev/null 2>&1; then
    echo "✅ Script hoạt động bình thường"
else
    echo "❌ Script có lỗi, hãy kiểm tra lại"
    exit 1
fi

# Hiển thị hướng dẫn cài đặt crontab
echo ""
echo "📋 HƯỚNG DẪN CÀI ĐẶT CRONTAB:"
echo "=============================="
echo ""
echo "1. Mở crontab editor:"
echo "   crontab -e"
echo ""
echo "2. Thêm các dòng sau vào cuối file:"
echo ""
echo "# VPS Manager Cron Jobs"
echo "0 2 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh zingproxy-sync"
echo "0 6 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh bitlaunch-apis"
echo "30 6 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh bitlaunch-vps"
echo "0 7 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh zingproxy-update"
echo "0 8 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh cloudfly-apis"
echo "30 8 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh cloudfly-vps"
echo "0 9 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh notifications"
echo "0 10 * * 0 /home/ubuntu/vps-manager/scripts/cron_job.sh weekly"
echo "0 */6 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh zingproxy-update"
echo "0 */2 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh zingproxy-sync"
echo ""
echo "3. Lưu và thoát (Ctrl+X, Y, Enter trong nano)"
echo ""
echo "4. Kiểm tra crontab đã được cài đặt:"
echo "   crontab -l"
echo ""
echo "5. Xem log:"
echo "   tail -f /home/ubuntu/vps-manager/logs/cron_job.log"
echo ""

# Tùy chọn tự động cài đặt
read -p "🤖 Bạn có muốn tự động cài đặt crontab không? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 Cài đặt crontab tự động..."
    
    # Backup crontab hiện tại
    crontab -l > /home/ubuntu/vps-manager/scripts/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true
    
    # Thêm VPS Manager jobs vào crontab
    (crontab -l 2>/dev/null; echo ""; echo "# VPS Manager Cron Jobs - Installed $(date)"; cat /home/ubuntu/vps-manager/scripts/crontab_example.txt) | crontab -
    
    echo "✅ Crontab đã được cài đặt thành công!"
    echo "📋 Xem crontab hiện tại: crontab -l"
    echo "📝 Xem log: tail -f /home/ubuntu/vps-manager/logs/cron_job.log"
else
    echo "📝 Hãy làm theo hướng dẫn trên để cài đặt thủ công"
fi

echo ""
echo "🎉 Cài đặt hoàn tất!"
echo ""
echo "📚 CÁC LỆNH HỮU ÍCH:"
echo "==================="
echo "• Xem crontab: crontab -l"
echo "• Sửa crontab: crontab -e"
echo "• Xóa crontab: crontab -r"
echo "• Xem log: tail -f /home/ubuntu/vps-manager/logs/cron_job.log"
echo "• Test script: /home/ubuntu/vps-manager/scripts/cron_job.sh notifications"
echo "• Chạy tất cả: /home/ubuntu/vps-manager/scripts/cron_job.sh all"
echo ""
echo "⚠️  LƯU Ý:"
echo "• Tắt scheduler trong VPS Manager để tránh xung đột"
echo "• Kiểm tra log thường xuyên để đảm bảo hoạt động bình thường"
echo "• Backup crontab trước khi thay đổi: crontab -l > backup.txt"
