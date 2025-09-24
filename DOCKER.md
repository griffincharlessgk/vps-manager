# 🐳 Docker Deployment Guide

Hướng dẫn triển khai VPS Manager với Docker và bảo vệ dữ liệu khỏi bị mất.

## 📁 Volume Mounts

### Dữ Liệu Quan Trọng Được Mount

| Thư mục | Mô tả | Tầm quan trọng |
|---------|-------|----------------|
| `./instance/` | Database files | 🔴 CRITICAL |
| `./logs/` | Application logs | 🔴 CRITICAL |
| `./scripts/` | Cron job scripts | 🔴 CRITICAL |
| `./.env` | Environment variables | 🔴 CRITICAL |
| `./backups/` | Backup files | 🔴 CRITICAL |
| `./production_keys_backup.txt` | Production keys | 🔴 CRITICAL |

## 🚀 Triển Khai

### Development
```bash
# Sử dụng docker-compose.yml cơ bản
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng
docker-compose down
```

### Production
```bash
# Sử dụng docker-compose.prod.yml với cấu hình nâng cao
docker-compose -f docker-compose.prod.yml up -d

# Xem logs
docker-compose -f docker-compose.prod.yml logs -f

# Dừng
docker-compose -f docker-compose.prod.yml down
```

## 💾 Backup & Restore

### Tự Động Backup
```bash
# Chạy backup thủ công
./scripts/backup.sh

# Thêm vào crontab để backup tự động
0 2 * * * /home/ubuntu/vps-manager/scripts/backup.sh
```

### Restore Dữ Liệu
```bash
# Xem danh sách backup
ls -la backups/

# Restore từ backup
./scripts/restore.sh 20240922_143000

# Restore từ file cụ thể
tar -xzf backups/vps_manager_backup_20240922_143000.tar.gz
```

## 🔧 Cấu Hình

### Environment Variables
```bash
# Tạo file .env
cp env.example .env

# Chỉnh sửa .env
nano .env
```

### Database
```bash
# SQLite (default)
DATABASE_URL=sqlite:///instance/users.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@postgres:5432/vps_manager
```

## 📊 Monitoring

### Health Check
```bash
# Kiểm tra trạng thái
curl http://localhost:5000/me

# Xem logs
docker-compose logs -f app

# Xem resource usage
docker stats
```

### Logs
```bash
# Application logs
docker-compose logs app

# All services
docker-compose logs

# Follow logs
docker-compose logs -f app
```

## 🛠️ Troubleshooting

### Container Không Khởi Động
```bash
# Xem logs
docker-compose logs app

# Kiểm tra cấu hình
docker-compose config

# Rebuild image
docker-compose build --no-cache
```

### Mất Dữ Liệu
```bash
# Kiểm tra volume mounts
docker-compose exec app ls -la /app/instance/

# Restore từ backup
./scripts/restore.sh <backup_name>
```

### Permission Issues
```bash
# Sửa quyền
sudo chown -R 1000:1000 instance/ logs/ backups/

# Hoặc chạy với quyền root
docker-compose exec --user root app chown -R 1000:1000 /app/instance/
```

## 🔒 Security

### Production Security
```yaml
# Trong docker-compose.prod.yml
security_opt:
  - no-new-privileges:true
user: "1000:1000"
```

### Environment Security
```bash
# Không commit .env
echo ".env" >> .gitignore

# Sử dụng secrets
docker secret create db_password ./db_password.txt
```

## 📈 Performance

### Resource Limits
```yaml
# Trong docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

### Log Rotation
```yaml
# Trong docker-compose.prod.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔄 Updates

### Update Application
```bash
# Pull latest code
git pull

# Rebuild và restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Update Dependencies
```bash
# Update requirements.txt
pip freeze > requirements.txt

# Rebuild image
docker-compose build --no-cache
```

## 📋 Maintenance

### Daily Tasks
```bash
# Backup dữ liệu
./scripts/backup.sh

# Kiểm tra logs
docker-compose logs --tail=100 app

# Clean up old images
docker image prune -f
```

### Weekly Tasks
```bash
# Full backup
./scripts/backup.sh

# Update system
docker-compose pull
docker-compose up -d

# Clean up
docker system prune -f
```

## 🚨 Emergency Recovery

### Nếu Container Bị Lỗi
```bash
# Dừng tất cả
docker-compose down

# Khôi phục từ backup
./scripts/restore.sh <latest_backup>

# Khởi động lại
docker-compose up -d
```

### Nếu Mất Dữ Liệu
```bash
# Kiểm tra backup
ls -la backups/

# Restore từ backup gần nhất
./scripts/restore.sh <backup_name>

# Kiểm tra dữ liệu
docker-compose exec app ls -la /app/instance/
```

## 📞 Support

Nếu gặp vấn đề:

1. Kiểm tra logs: `docker-compose logs`
2. Kiểm tra volume mounts: `docker-compose exec app ls -la /app/`
3. Restore từ backup: `./scripts/restore.sh <backup_name>`
4. Tạo issue trên GitHub

---

**💡 Lưu ý**: Luôn backup dữ liệu trước khi thực hiện bất kỳ thay đổi nào!
