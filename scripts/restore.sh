#!/bin/bash

# VPS Manager Restore Script
# Khôi phục dữ liệu từ backup

set -e

# Cấu hình
BACKUP_DIR="/home/ubuntu/vps-manager/backups"

# Kiểm tra tham số
if [ $# -eq 0 ]; then
    echo "❌ Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    ls -la "$BACKUP_DIR" | grep "vps_manager_backup_" | awk '{print $9}' | sed 's/vps_manager_backup_//' | sed 's/.tar.gz//'
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_FILE="$BACKUP_DIR/vps_manager_backup_${BACKUP_NAME}.tar.gz"

# Kiểm tra file backup
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    echo ""
    echo "Available backups:"
    ls -la "$BACKUP_DIR" | grep "vps_manager_backup_" | awk '{print $9}' | sed 's/vps_manager_backup_//' | sed 's/.tar.gz//'
    exit 1
fi

echo "🔄 Starting restore from: $BACKUP_NAME"

# Xác nhận restore
read -p "⚠️  This will overwrite current data. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# Tạo backup hiện tại trước khi restore
echo "💾 Creating current data backup..."
./scripts/backup.sh

# Dừng ứng dụng nếu đang chạy
echo "⏹️  Stopping application..."
docker-compose down 2>/dev/null || true

# Restore dữ liệu
echo "📦 Extracting backup..."
cd /home/ubuntu/vps-manager
tar -xzf "$BACKUP_FILE"

# Khôi phục quyền
echo "🔐 Restoring permissions..."
chmod +x scripts/*.sh
chmod 644 .env
chmod 600 production_keys_backup.txt 2>/dev/null || true

# Khởi động lại ứng dụng
echo "🚀 Starting application..."
docker-compose up -d

# Kiểm tra trạng thái
echo "🔍 Checking application status..."
sleep 10
if curl -f http://localhost:5000/me > /dev/null 2>&1; then
    echo "✅ Application restored successfully!"
    echo "🌐 Access: http://localhost:5000"
else
    echo "❌ Application may not be running properly"
    echo "📝 Check logs: docker-compose logs"
fi

echo ""
echo "🎉 Restore completed!"
echo "📋 Restored from: $BACKUP_NAME"
echo "📅 Restore time: $(date)"
