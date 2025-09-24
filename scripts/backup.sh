#!/bin/bash

# VPS Manager Backup Script
# Tự động backup dữ liệu quan trọng

set -e

# Cấu hình
BACKUP_DIR="/home/ubuntu/vps-manager/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="vps_manager_backup_${DATE}"

# Tạo thư mục backup
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting backup: $BACKUP_NAME"

# Backup database
echo "📊 Backing up database..."
if [ -f "instance/users.db" ]; then
    cp instance/users.db "$BACKUP_DIR/users_${DATE}.db"
    echo "✅ Database backed up"
else
    echo "⚠️  Database file not found"
fi

# Backup logs
echo "📝 Backing up logs..."
if [ -d "logs" ]; then
    tar -czf "$BACKUP_DIR/logs_${DATE}.tar.gz" logs/
    echo "✅ Logs backed up"
else
    echo "⚠️  Logs directory not found"
fi

# Backup instance directory
echo "💾 Backing up instance directory..."
if [ -d "instance" ]; then
    tar -czf "$BACKUP_DIR/instance_${DATE}.tar.gz" instance/
    echo "✅ Instance directory backed up"
else
    echo "⚠️  Instance directory not found"
fi

# Backup scripts
echo "🔧 Backing up scripts..."
if [ -d "scripts" ]; then
    tar -czf "$BACKUP_DIR/scripts_${DATE}.tar.gz" scripts/
    echo "✅ Scripts backed up"
else
    echo "⚠️  Scripts directory not found"
fi

# Backup environment files
echo "⚙️  Backing up environment files..."
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/env_${DATE}.env"
    echo "✅ Environment file backed up"
fi

if [ -f "production_keys_backup.txt" ]; then
    cp production_keys_backup.txt "$BACKUP_DIR/production_keys_backup_${DATE}.txt"
    echo "✅ Production keys backed up"
fi

# Tạo backup tổng hợp
echo "📦 Creating comprehensive backup..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" \
    instance/ \
    logs/ \
    scripts/ \
    .env \
    production_keys_backup.txt \
    2>/dev/null || true

echo "✅ Comprehensive backup created: ${BACKUP_NAME}.tar.gz"

# Xóa backup cũ (giữ lại 7 ngày)
echo "🧹 Cleaning old backups..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.db" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.env" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.txt" -mtime +7 -delete

echo "✅ Old backups cleaned"

# Hiển thị thông tin backup
echo ""
echo "📋 Backup Summary:"
echo "=================="
echo "Backup name: $BACKUP_NAME"
echo "Backup directory: $BACKUP_DIR"
echo "Files created:"
ls -la "$BACKUP_DIR" | grep "$DATE"

echo ""
echo "🎉 Backup completed successfully!"
echo "💡 To restore: tar -xzf $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
