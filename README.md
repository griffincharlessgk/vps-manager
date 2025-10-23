# 🚀 VPS Manager

A comprehensive VPS and account management system with automated notifications, multi-provider support, multi-currency balance tracking, and intelligent alert system.

## ✨ Features

### 🌐 Multi-Provider Support

- **BitLaunch**: VPS provisioning with USD balance tracking
- **ZingProxy**: Proxy management with VND balance tracking
- **CloudFly**: VPS and cloud services with VND balance tracking
- **Manual Accounts**: Support for custom account management

### 🔔 Intelligent Alert System

- **Automated Notifications**: Rocket.Chat integration with customizable schedules
- **Balance Alerts**: Multi-currency support (USD, VND) with provider-specific thresholds
  - BitLaunch: Alert when balance < $5 USD
  - ZingProxy: Alert when balance < 100,000 VND
  - CloudFly: Alert when balance < 100,000 VND
- **Expiry Warnings**: Customizable warning periods (3-7 days before expiry)
- **Real-time Updates**: Automatic balance and status updates every 6-12 hours

### 👥 User Management

- Role-based access control (Admin/User)
- Per-user notification settings
- Multi-user support with isolated data

### 🔐 Security Features

- Data encryption at rest using Fernet
- Secure API key storage
- Session management with secure cookies
- Input validation and sanitization
- Security event logging

### 📊 Real-time Monitoring

- Unified dashboard for all providers
- Multi-currency balance display
- VPS status tracking
- Proxy inventory management
- Automated health checks

## 🔧 Technology Stack

- **Backend**: Flask 3.0+, SQLAlchemy 2.0+
- **Database**: PostgreSQL (production), SQLite (development)
- **Scheduler**: APScheduler (16 automated jobs)
- **Encryption**: Cryptography (Fernet symmetric encryption)
- **API Integration**: pybitlaunch, requests
- **Notifications**: Rocket.Chat API
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **Deployment**: Docker, Gunicorn

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+ (for production) or SQLite (for development)
- Docker (optional)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd vps-manager
   ```
2. **Create virtual environment**

   ```bash
   python -m venv venv
   # Linux/macOS
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables**

   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```
5. **Generate encryption key** (if not set)

   ```bash
   python scripts/generate_keys.py
   ```
6. **Initialize database**

   ```bash
   python scripts/init_db.py
   ```

## 🏃‍♂️ Running the Application

### Method 1: Using run_app.py (Recommended)

```bash
python run_app.py
```

### Method 2: Using Flask CLI

```bash
export FLASK_APP=ui.app
flask run
```

### Method 3: Using Python module

```bash
python -m flask --app ui.app run
```

### Access the Application

Open your browser and navigate to:

```
http://localhost:5000
```

**Default Credentials:**

- Username: `admin`
- Password: Set during database initialization

## 🔐 Environment Variables

| Variable                  | Description                              | Required      | Default                         |
| ------------------------- | ---------------------------------------- | ------------- | ------------------------------- |
| `SECRET_KEY`            | Flask secret key for session management  | Yes           | -                               |
| `DATABASE_URL`          | Database connection string               | No            | `sqlite:///instance/users.db` |
| `ENCRYPTION_KEY`        | Fernet encryption key for sensitive data | **Yes** | Auto-generated (save it!)       |
| `LOG_LEVEL`             | Logging level (DEBUG/INFO/WARNING/ERROR) | No            | `INFO`                        |
| `SESSION_COOKIE_SECURE` | Enable secure cookies (HTTPS only)       | No            | `False`                       |
| `ALLOWED_ORIGINS`       | CORS allowed origins                     | No            | `*`                           |

### ⚠️ Important: ENCRYPTION_KEY

The `ENCRYPTION_KEY` is critical for decrypting stored API credentials. If you lose this key, you'll need to re-enter all API credentials.

```bash
# Save your encryption key to a secure backup
echo "ENCRYPTION_KEY=$(grep ENCRYPTION_KEY .env)" > production_keys_backup.txt
```

## 📊 Database Schema

### Core Tables

#### Users & Authentication

- **users**: User accounts with role-based permissions
  - `id`, `username`, `email`, `password_hash`, `role`
  - `notify_days`, `notify_hour`, `notify_minute`

#### Manual Management

- **vps**: Manually tracked VPS instances
  - `id`, `name`, `ip`, `provider`, `expiry`, `status`
- **accounts**: Manually tracked accounts
  - `id`, `username`, `service`, `expiry`, `notes`

#### BitLaunch Integration

- **bitlaunch_apis**: BitLaunch API credentials (encrypted)
  - `id`, `email`, `api_token`, `balance`, `account_limit`
  - `last_updated`, `user_id`
- **bitlaunch_vps**: VPS instances from BitLaunch
  - `id`, `instance_id`, `host`, `ip`, `status`, `created_at`

#### ZingProxy Integration

- **zingproxy_accounts**: ZingProxy account credentials (encrypted)
  - `id`, `email`, `password`, `balance`, `expired_at`
  - `last_updated`, `user_id`
- **zingproxies**: Proxy inventory from ZingProxy
  - `id`, `account_id`, `proxy_type`, `location`, `ip`, `port`

#### CloudFly Integration

- **cloudfly_apis**: CloudFly API credentials (encrypted)
  - `id`, `email`, `api_key`, `balance`, `status`
  - `last_updated`, `user_id`
- **cloudfly_vps**: VPS instances from CloudFly
  - `id`, `instance_id`, `name`, `ip`, `status`, `created_at`

#### Notifications

- **rocketchat_configs**: Rocket.Chat notification settings
  - `id`, `user_id`, `server_url`, `auth_token`, `user_id_rocket`
  - `room_id`, `is_active`

## 🔌 API Endpoints

### Authentication

- `POST /login` - User login
- `POST /logout` - User logout
- `GET /me` - Get current user information

### VPS Management

- `GET /api/vps` - List all VPS (manual + providers)
- `POST /api/vps` - Add manual VPS
- `PUT /api/vps/<id>` - Update VPS information
- `DELETE /api/vps/<id>` - Delete VPS

### Account Management

- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Add manual account
- `PUT /api/accounts/<id>` - Update account
- `DELETE /api/accounts/<id>` - Delete account

### BitLaunch Integration

- `POST /api/bitlaunch-save-api` - Save API credentials
- `GET /api/bitlaunch-apis` - List all BitLaunch APIs
- `POST /api/bitlaunch-update-api/<id>` - Update specific API
- `POST /api/bitlaunch-update-all` - Update all APIs
- `DELETE /api/bitlaunch-delete/<id>` - Delete API
- `GET /api/bitlaunch-vps` - List BitLaunch VPS instances

### ZingProxy Integration

- `POST /api/zingproxy-login` - Add ZingProxy account
- `GET /api/zingproxy-accounts` - List all accounts
- `POST /api/zingproxy-update-account/<id>` - Update account info
- `POST /api/zingproxy-update-proxies/<id>` - Sync proxies
- `GET /api/zingproxy-proxies` - List all proxies
- `DELETE /api/zingproxy-delete-account/<id>` - Delete account

### CloudFly Integration

- `POST /api/cloudfly-save-api` - Save API credentials
- `GET /api/cloudfly-apis` - List all CloudFly APIs
- `POST /api/cloudfly-update-api/<id>` - Update specific API
- `POST /api/cloudfly-update-all` - Update all APIs
- `DELETE /api/cloudfly-delete/<id>` - Delete API
- `GET /api/cloudfly-vps` - List CloudFly VPS instances

### Rocket.Chat Notifications

- `POST /api/rocket-chat-config` - Save Rocket.Chat configuration
- `GET /api/rocket-chat-config` - Get current configuration
- `POST /api/rocket-chat-test` - Test notification
- `POST /api/rocket-chat-send-daily-summary` - Send daily summary
- `POST /api/rocket-chat-send-account-notification` - Send account alerts

### User Management (Admin only)

- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user

## ⏰ Automated Scheduler Jobs

The system runs 16 automated background jobs:

### Balance & Status Updates

| Job                              | Frequency      | Description                               |
| -------------------------------- | -------------- | ----------------------------------------- |
| `bitlaunch_update`             | Daily at 06:00 | Update BitLaunch balance and account info |
| `bitlaunch_vps_update`         | Daily at 06:30 | Sync BitLaunch VPS instances              |
| `zingproxy_update`             | Daily at 07:00 | Update ZingProxy balance and account info |
| `zingproxy_update_interval`    | Every 6 hours  | Frequent ZingProxy balance updates        |
| `cloudfly_update`              | Daily at 08:00 | Update CloudFly balance and account info  |
| `cloudfly_update_interval`     | Every 6 hours  | Frequent CloudFly balance updates         |
| `cloudfly_vps_update_interval` | Every 6 hours  | Sync CloudFly VPS instances               |

### Notifications & Alerts

| Job                                | Frequency       | Description                           |
| ---------------------------------- | --------------- | ------------------------------------- |
| `account_alerts_12h`             | Every 12 hours  | Check and send balance/expiry alerts  |
| `expiry_warnings`                | Every 5 minutes | Check expiry at configured user times |
| `daily_summary`                  | Every 5 minutes | Check for daily summary time          |
| `rocketchat_daily_notifications` | Daily at 09:00  | Send comprehensive daily report       |
| `weekly_report`                  | Sunday at 10:00 | Send weekly summary report            |

### Proxy Management

| Job                             | Frequency      | Description                    |
| ------------------------------- | -------------- | ------------------------------ |
| `zingproxy_proxy_sync`        | Every 2 hours  | Sync proxy inventory           |
| `zingproxy_proxy_sync_daily`  | Daily at 08:00 | Daily proxy sync               |
| `auto_sync_zingproxy_proxies` | Daily at 02:00 | Automated overnight proxy sync |

## 🔔 Alert Thresholds

### Balance Alerts

- **BitLaunch**: Alerts when balance < **$5 USD**
- **ZingProxy**: Alerts when balance < **100,000 VND**
- **CloudFly**: Alerts when balance < **100,000 VND**

### Expiry Alerts

- **Default**: 3 days before expiry
- **Configurable**: Per-user setting (1-30 days)

### Notification Frequency

- **Balance Alerts**: Every 12 hours
- **Expiry Warnings**: Daily at user-configured time
- **Daily Summary**: 09:00 AM (configurable)
- **Weekly Report**: Sunday 10:00 AM

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f vps-manager

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Manual Docker Build

```bash
# Build image
docker build -t vps-manager:latest .

# Run container
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e ENCRYPTION_KEY=your-encryption-key \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  --name vps-manager \
  vps-manager:latest

#iew logs
docker logs -f vps-manager
```

## 📈 Monitoring and Logs

### Log Files

- `logs/app.log` - General application logs (INFO level)
- `logs/scheduler.log` - Scheduler job execution logs
- `logs/security.log` - Security events and authentication

### Log Monitoring

```bash
# Watch all logs
tail -f logs/app.log

# Watch scheduler jobs
tail -f logs/app.log | grep Scheduler

# Watch alerts
tail -f logs/app.log | grep -E "Alert|balance|expiry"

# Watch API updates
tail -f logs/app.log | grep -E "BitLaunch|ZingProxy|CloudFly"
```

### Health Checks

```bash
# Check app health (Docker HEALTHCHECK target)
curl http://localhost:5000/health

# Check current user (optional)
curl http://localhost:5000/me

# Check scheduler status (local dev)
python -c "from core.scheduler import get_scheduler; print(get_scheduler().running)"
```

### Enabling Scheduler in Docker

This project enables the scheduler inside the container when `ENABLE_SCHEDULER=true` and a single Gunicorn worker is used.

```bash
docker run -d \
  -p 5000:5000 \
  --env-file .env \
  -e ENABLE_SCHEDULER=true \
  --name vps-manager \
  vps-manager:latest

# Verify scheduler running
docker exec vps-manager tail -n 50 /app/logs/app.log | grep Scheduler
```

## 🔄 Backup and Maintenance

### Database Backup

#### PostgreSQL

```bash
# Backup
pg_dump -h localhost -U vps_user vps_manager > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -U vps_user vps_manager < backup_20241006.sql
```

#### SQLite

```bash
# Backup
cp instance/users.db backups/users_$(date +%Y%m%d).db

# Restore
cp backups/users_20241006.db instance/users.db
```

### Encryption Key Backup

**⚠️ CRITICAL**: Always backup your encryption key!

```bash
# Save encryption key
grep ENCRYPTION_KEY .env > production_keys_backup.txt
chmod 600 production_keys_backup.txt
```

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/vps-manager"

# Backup database
sqlite3 instance/users.db ".backup $BACKUP_DIR/db_$DATE.db"

# Backup .env
cp .env $BACKUP_DIR/env_$DATE.txt

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Encryption Key Error

```
Error: ENCRYPTION_KEY not found or invalid
```

**Solution:**

```bash
# Check if ENCRYPTION_KEY is set
grep ENCRYPTION_KEY .env

# If missing, generate new key (will require re-entering all API credentials)
python scripts/generate_keys.py

# Or restore from backup
cp production_keys_backup.txt .env
```

#### 2. Decryption Error for API Credentials

```
Error: Unable to decrypt API credentials
```

**Solution:**

```bash
# Ensure ENCRYPTION_KEY matches the one used to encrypt data
# Check backup file
cat production_keys_backup.txt

# Update .env with correct key
# Then restart application
```

#### 3. Scheduler Not Running

```bash
# Check scheduler status
python -c "from core.scheduler import get_scheduler; s = get_scheduler(); print(f'Running: {s.running}, Jobs: {len(s.get_jobs())}')"

# Restart application
pkill -f run_app.py
python run_app.py
```

#### 4. API Update Failures

```
Error: 401 Unauthorized
```

**Solution:**

1. Delete the old API key from UI
2. Re-add the API key (will be encrypted with current ENCRYPTION_KEY)
3. Test the API connection

#### 5. Rocket.Chat Notifications Not Sending

```bash
# Test Rocket.Chat configuration
curl -X POST http://localhost:5000/api/rocket-chat-test

# Check logs
tail -50 logs/app.log | grep -i rocketchat

# Verify configuration
# Go to Settings > Rocket.Chat in UI and test connection
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with Flask debug mode
export FLASK_ENV=development
python run_app.py
```

### View Scheduler Jobs

```bash
# List all scheduled jobs
python -c "
from core.scheduler import get_scheduler
from datetime import datetime

scheduler = get_scheduler()
print(f'Total Jobs: {len(scheduler.get_jobs())}')
print()
for job in scheduler.get_jobs():
    print(f'{job.id:30} | Next run: {job.next_run_time}')
"
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test file
pytest tests/test_scheduler.py -v

# Run with coverage
pytest --cov=core --cov=ui tests/
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 core/ ui/ tests/

# Type checking
mypy core/ ui/
```

### Adding New Provider

1. Create API client in `core/api_clients/new_provider.py`
2. Add database model in `core/models.py`
3. Add manager methods in `core/manager.py`
4. Add scheduler jobs in `core/scheduler.py`
5. Add UI routes in `ui/app.py`
6. Create frontend templates in `ui/templates/`
7. Update `README.md` with new provider info

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Message Guidelines

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review logs in `logs/` directory
3. Check [Issues](https://github.com/your-repo/issues) on GitHub
4. Contact the development team

## 🎯 Roadmap

### Version 2.0

- [ ] Multi-language support (English, Vietnamese, Chinese)
- [ ] Mobile-responsive UI improvements
- [ ] Advanced analytics dashboard with charts
- [ ] WebSocket real-time notifications
- [ ] API rate limiting and throttling
- [ ] Two-factor authentication (2FA)

### Version 2.1

- [ ] More provider integrations (AWS, DigitalOcean, Vultr)
- [ ] Custom alert rules engine
- [ ] Export reports to PDF/Excel
- [ ] Budget tracking and forecasting
- [ ] Team collaboration features

### Version 2.2

- [ ] Mobile app (iOS/Android)
- [ ] Advanced backup and restore
- [ ] Audit log with user activity tracking
- [ ] Integration with monitoring tools (Grafana, Prometheus)
- [ ] AI-powered cost optimization suggestions

## 📊 System Requirements

### Minimum Requirements

- **CPU**: 1 core
- **RAM**: 512 MB
- **Storage**: 1 GB
- **Python**: 3.11+

### Recommended for Production

- **CPU**: 2+ cores
- **RAM**: 2 GB+
- **Storage**: 10 GB+ (with logs retention)
- **Database**: PostgreSQL 12+
- **OS**: Ubuntu 20.04+ / Debian 11+

## 🙏 Acknowledgments

- Flask team for the excellent web framework
- SQLAlchemy team for the powerful ORM
- Rocket.Chat team for the messaging platform
- Bootstrap team for the UI framework
- APScheduler team for the scheduling library
- All contributors and users of this project

## 📚 Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Database Schema](docs/DATABASE.md) - Detailed schema documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment guide
- [Security Guide](docs/SECURITY.md) - Security best practices

---

**Version**: 1.0.0
**Last Updated**: October 6, 2025
**Made with ❤️ for VPS management**
