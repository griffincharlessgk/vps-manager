# VPS Manager Cron Jobs

Hệ thống cron jobs thay thế cho APScheduler, cho phép chạy các tác vụ định kỳ thông qua cron job của hệ thống.

## 📁 Files

- `cron_job.sh` - Script chính để thực hiện các tác vụ
- `install_cron.sh` - Script cài đặt và cấu hình tự động
- `crontab_example.txt` - File mẫu cấu hình crontab
- `README_CRON.md` - Hướng dẫn sử dụng

## 🚀 Cài Đặt Nhanh

```bash
# Chạy script cài đặt tự động
./scripts/install_cron.sh

# Hoặc cài đặt thủ công
chmod +x scripts/cron_job.sh
crontab -e
# Thêm nội dung từ crontab_example.txt
```

## 📋 Các Tác Vụ Có Sẵn

### ZingProxy
- `zingproxy-sync` - Đồng bộ proxy từ ZingProxy
- `zingproxy-update` - Cập nhật thông tin tài khoản ZingProxy

### BitLaunch
- `bitlaunch-apis` - Cập nhật thông tin tài khoản BitLaunch
- `bitlaunch-vps` - Cập nhật danh sách VPS BitLaunch

### CloudFly
- `cloudfly-apis` - Cập nhật thông tin tài khoản CloudFly
- `cloudfly-vps` - Cập nhật danh sách VPS CloudFly

### Notifications
- `notifications` - Gửi thông báo hết hạn và chi tiết tài khoản
- `daily` - Chạy tất cả tác vụ hàng ngày
- `weekly` - Gửi báo cáo tuần

## 🕐 Lịch Trình Mặc Định

```
02:00 - Đồng bộ proxy ZingProxy
06:00 - Cập nhật BitLaunch APIs
06:30 - Cập nhật BitLaunch VPS
07:00 - Cập nhật ZingProxy accounts
08:00 - Cập nhật CloudFly APIs + Đồng bộ ZingProxy
08:30 - Cập nhật CloudFly VPS
09:00 - Gửi thông báo hết hạn và chi tiết tài khoản
10:00 - Gửi báo cáo tuần (Chủ nhật)

Mỗi 2 giờ - Đồng bộ ZingProxy
Mỗi 6 giờ - Cập nhật ZingProxy + CloudFly
```

## 🔧 Sử Dụng

### Chạy Script Thủ Công

```bash
# Chạy tất cả tác vụ
./scripts/cron_job.sh all

# Chạy tác vụ cụ thể
./scripts/cron_job.sh notifications
./scripts/cron_job.sh zingproxy-sync
./scripts/cron_job.sh daily

# Xem trợ giúp
./scripts/cron_job.sh
```

### Cấu Hình Crontab

```bash
# Mở crontab editor
crontab -e

# Xem crontab hiện tại
crontab -l

# Xóa tất cả crontab
crontab -r
```

### Ví Dụ Crontab

```bash

# Chạy tác vụ hàng ngày lúc 9:00 sáng
0 9 * * * /home/ubuntu/vps-manager/scripts/cron_job.sh daily

# Chạy báo cáo tuần mỗi Chủ nhật
0 10 * * 0 /home/ubuntu/vps-manager/scripts/cron_job.sh weekly
```

## 📊 Monitoring

### Xem Log

```bash
# Xem log real-time
tail -f /home/ubuntu/vps-manager/logs/cron_job.log

# Xem log cuối cùng
tail -n 50 /home/ubuntu/vps-manager/logs/cron_job.log

# Tìm kiếm lỗi
grep "ERROR" /home/ubuntu/vps-manager/logs/cron_job.log
```

### Kiểm Tra Trạng Thái

```bash
# Kiểm tra cron service
sudo systemctl status cron

# Xem cron jobs đang chạy
ps aux | grep cron

# Kiểm tra log hệ thống
sudo journalctl -u cron
```

## 🛠️ Troubleshooting

### Lỗi Thường Gặp

1. **Script không chạy được**
   ```bash
   # Kiểm tra quyền thực thi
   ls -la scripts/cron_job.sh
   
   # Cấp quyền thực thi
   chmod +x scripts/cron_job.sh
   ```

2. **VPS Manager server không chạy**
   ```bash
   # Kiểm tra server
   curl http://localhost:5000/me
   
   # Khởi động server
   python run_app.py
   ```

3. **Cron job không chạy**
   ```bash
   # Kiểm tra cron service
   sudo systemctl status cron
   
   # Khởi động cron service
   sudo systemctl start cron
   ```

4. **Log không được ghi**
   ```bash
   # Kiểm tra quyền ghi log
   ls -la logs/
   
   # Tạo thư mục logs
   mkdir -p logs
   ```

### Debug

```bash
# Chạy script với output chi tiết
bash -x scripts/cron_job.sh notifications

# Test API endpoint
curl -v http://localhost:5000/api/send-expiry-notifications

# Kiểm tra crontab
crontab -l | grep vps-manager
```

## 🔄 Migration từ Scheduler

1. **Tắt Scheduler**
   - Comment hoặc xóa code khởi động scheduler trong `ui/app.py`
   - Restart VPS Manager

2. **Cài Đặt Cron Jobs**
   ```bash
   ./scripts/install_cron.sh
   ```

3. **Kiểm Tra Hoạt Động**
   ```bash
   # Test thủ công
   ./scripts/cron_job.sh notifications
   
   # Xem log
   tail -f logs/cron_job.log
   ```

## 📈 Performance

### Tối Ưu Hóa

1. **Giảm Tần Suất**
   - Chỉ chạy các tác vụ cần thiết
   - Tăng interval cho các tác vụ không quan trọng

2. **Log Rotation**
   ```bash
   # Thêm vào crontab
   0 0 * * 0 find /home/ubuntu/vps-manager/logs -name "*.log" -mtime +28 -delete
   ```

3. **Monitoring**
   - Sử dụng monitoring tools như Nagios, Zabbix
   - Thiết lập alert khi có lỗi

## 🔒 Security

### Best Practices

1. **Quyền File**
   ```bash
   chmod 750 scripts/cron_job.sh
   chmod 640 logs/cron_job.log
   ```

2. **User Isolation**
   - Chạy cron jobs với user riêng
   - Không sử dụng root user

3. **Log Security**
   - Không ghi sensitive data vào log
   - Rotate log files thường xuyên

## 📞 Support

Nếu gặp vấn đề, hãy:

1. Kiểm tra log: `tail -f logs/cron_job.log`
2. Test script: `./scripts/cron_job.sh notifications`
3. Kiểm tra server: `curl http://localhost:5000/me`
4. Xem crontab: `crontab -l`
