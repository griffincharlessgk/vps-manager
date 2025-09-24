# 🚀 VPS Manager

A comprehensive VPS and account management system with automated notifications, multi-provider support, and user management.

## ✨ Features

- **Multi-Provider Support**: BitLaunch, ZingProxy, CloudFly
- **Automated Notifications**: RocketChat integration with customizable schedules
- **Cron Job System**: Replaceable scheduler with system cron jobs
- **User Management**: Role-based access control with admin/user permissions
- **Data Encryption**: Sensitive data encrypted at rest using Fernet
- **Real-time Monitoring**: Dashboard with expiry warnings and status tracking
- **API Integration**: Direct integration with provider APIs for real-time data
- **Proxy Management**: Automated proxy synchronization and management
- **Cross-Platform**: Support for Windows, Linux, and macOS

## 🔧 Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: PostgreSQL (production), SQLite (development)
- **Scheduler**: System Cron Jobs (replaces APScheduler)
- **Encryption**: Cryptography (Fernet)
- **API Integration**: pybitlaunch, requests, custom clients
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Deployment**: Docker, Gunicorn
- **Notifications**: RocketChat API

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+ (for production)
- Docker (optional)
- Cron service (for automated tasks)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vps-manager
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
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

5. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

6. **Set up cron jobs (optional)**
   ```bash
   ./scripts/install_cron.sh
   ```

## 🏃‍♂️ Running the Application

### Method 1: Run from ui directory (Recommended)
```bash
cd ui
python -m flask run
```

### Method 2: Run from root directory with FLASK_APP
```bash
export FLASK_APP=ui.app
python -m flask run
```

### Method 3: Run directly with Python
```bash
cd ui
python app.py
```

### Method 4: Use --app flag from root directory
```bash
python -m flask --app ui.app run
```

### Access the Application
After running any of the above methods, open your browser and go to:
```
http://localhost:5000
```

## 🔐 Security Features

✅ **Environment Variables**: All sensitive configuration moved to environment variables
✅ **Data Encryption**: API keys, passwords, and tokens encrypted in database
✅ **Input Validation**: Comprehensive validation for all user inputs
✅ **Security Headers**: XSS protection, CSRF protection, and other security headers
✅ **Non-root Docker**: Container runs as non-root user
✅ **Logging**: Structured logging with security event tracking
✅ **Error Handling**: Proper error handling and logging
✅ **Cron Job Security**: Secure cron job execution with proper permissions

## 🌐 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | - |
| `DATABASE_URL` | Database connection string | No | `sqlite:///users.db` |
| `ENCRYPTION_KEY` | Encryption key for sensitive data | No | Auto-generated |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `SESSION_COOKIE_SECURE` | Secure cookies | No | `False` |
| `ALLOWED_ORIGINS` | CORS origins | No | `*` |

## 📊 Database Schema

### Core Tables
- `users`: User management and authentication
- `vps`: VPS information and expiry tracking
- `accounts`: Account management and expiry tracking
- `bitlaunch_apis`: BitLaunch API credentials
- `bitlaunch_vps`: VPS from BitLaunch
- `zingproxy_accounts`: ZingProxy account information
- `zingproxies`: Proxy information from ZingProxy
- `cloudfly_apis`: CloudFly API credentials
- `cloudfly_vps`: VPS from CloudFly
- `rocket_chat_configs`: RocketChat notification configurations
- `proxies`: Managed proxy information

## 🔌 API Endpoints

### Authentication
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /me` - Get current user info

### VPS Management
- `GET /api/vps` - List all VPS
- `POST /api/vps` - Add new VPS
- `PUT /api/vps/<id>` - Update VPS
- `DELETE /api/vps/<id>` - Delete VPS

### Account Management
- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Add new account
- `PUT /api/accounts/<id>` - Update account
- `DELETE /api/accounts/<id>` - Delete account

### BitLaunch Integration
- `POST /api/bitlaunch-save-api` - Save API credentials
- `GET /api/bitlaunch-apis` - List saved APIs
- `POST /api/bitlaunch-update-all` - Update all APIs
- `GET /api/update-bitlaunch-apis` - Update BitLaunch APIs (cron job)
- `GET /api/update-bitlaunch-vps` - Update BitLaunch VPS (cron job)

### ZingProxy Integration
- `POST /api/zingproxy-login` - Add ZingProxy account
- `GET /api/zingproxy-accounts` - List ZingProxy accounts
- `POST /api/zingproxy-update-proxies/<id>` - Update proxies
- `GET /api/update-zingproxy-accounts` - Update ZingProxy accounts (cron job)
- `GET /api/sync-zingproxy-proxies` - Sync ZingProxy proxies (cron job)

### CloudFly Integration
- `POST /api/cloudfly-save-api` - Save API credentials
- `GET /api/cloudfly-apis` - List saved APIs
- `GET /api/cloudfly/vps` - List CloudFly VPS
- `GET /api/update-cloudfly-apis` - Update CloudFly APIs (cron job)
- `GET /api/update-cloudfly-vps` - Update CloudFly VPS (cron job)

### Proxy Management
- `GET /api/proxies` - List all proxies
- `POST /api/proxies` - Add new proxy
- `PUT /api/proxies/<id>` - Update proxy
- `DELETE /api/proxies/<id>` - Delete proxy
- `GET /api/proxies/sync-status` - Get proxy sync status

### Notifications
- `GET /api/send-expiry-notifications` - Send expiry notifications (cron job)
- `GET /api/send-account-details` - Send account details (cron job)
- `GET /api/send-daily-summary` - Send daily summary (cron job)
- `GET /api/send-weekly-report` - Send weekly report (cron job)
- `GET /api/expiry-warnings` - Get expiry warnings

### RocketChat Integration
- `POST /api/rocket-chat/save-config` - Save RocketChat configuration
- `GET /api/rocket-chat/channels` - Get RocketChat channels
- `POST /api/rocket-chat/send-account-notification` - Send account notification
- `POST /api/rocket-chat/send-daily-summary` - Send daily summary
- `POST /api/rocket-chat/send-detailed-info` - Send detailed account info

## ⏰ Cron Job System

The system uses cron jobs instead of APScheduler for better reliability and system integration.

### Available Cron Jobs

- **ZingProxy Sync**: Every 2 hours and daily at 2:00 AM
- **BitLaunch Updates**: Daily at 6:00 AM (APIs) and 6:30 AM (VPS)
- **CloudFly Updates**: Daily at 8:00 AM (APIs) and 8:30 AM (VPS)
- **Notifications**: Daily at 9:00 AM (expiry + account details)
- **Weekly Reports**: Every Sunday at 10:00 AM

### Cron Job Management

```bash
# Install cron jobs
./scripts/install_cron.sh

# Manual execution
./scripts/cron_job.sh notifications
./scripts/cron_job.sh daily
./scripts/cron_job.sh zingproxy-sync

# View cron jobs
crontab -l

# Edit cron jobs
crontab -e
```

### Cron Job Scripts

- `scripts/cron_job.sh` - Main cron job script
- `scripts/install_cron.sh` - Installation script
- `scripts/crontab_example.txt` - Example crontab configuration
- `scripts/README_CRON.md` - Detailed cron job documentation

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker
```bash
# Build image
docker build -t vps-manager .

# Run container
docker run -p 5000:5000 -e DATABASE_URL=postgresql://... vps-manager
```

## 📈 Monitoring and Logs

### Log Files
- `logs/app.log` - General application logs
- `logs/error.log` - Error logs
- `logs/security.log` - Security events
- `logs/cron_job.log` - Cron job execution logs

### Health Checks
```bash
curl http://localhost:5000/me
curl http://localhost:5000/api/send-expiry-notifications
```

### Monitoring Cron Jobs
```bash
# View cron job logs
tail -f logs/cron_job.log

# Check cron service
sudo systemctl status cron

# View system cron logs
sudo journalctl -u cron
```

## 🔄 Backup and Maintenance

### Database Backup
```bash
# PostgreSQL
pg_dump vps_manager > backup.sql

# SQLite
cp instance/users.db backup.db
```

### Automated Backup
```bash
# Add to crontab for automated backup
0 2 * * * /path/to/backup_script.sh
```

### Log Rotation
```bash
# Automatic log rotation (included in crontab)
0 0 * * 0 find /home/ubuntu/vps-manager/logs -name "*.log" -mtime +28 -delete
```

## 🚨 Troubleshooting

### Common Issues

1. **Flask Application Not Found**
   - Make sure you're in the correct directory (`ui/` folder)
   - Use `export FLASK_APP=ui.app` when running from root directory
   - Or use `python -m flask --app ui.app run` from root directory

2. **Database Connection Errors**
   - Check `DATABASE_URL` environment variable
   - Ensure database is running
   - Verify credentials

3. **Encryption Errors**
   - Ensure `ENCRYPTION_KEY` is set
   - Don't change encryption key after data is stored

4. **Cron Jobs Not Running**
   - Check cron service: `sudo systemctl status cron`
   - Verify crontab: `crontab -l`
   - Check logs: `tail -f logs/cron_job.log`
   - Test manually: `./scripts/cron_job.sh notifications`

5. **RocketChat Notifications Not Working**
   - Verify RocketChat configuration in UI
   - Check API credentials and room IDs
   - Test endpoint: `curl http://localhost:5000/api/send-expiry-notifications`

### Debug Mode
```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
cd ui
python -m flask run
```

### Testing Cron Jobs
```bash
# Test individual tasks
./scripts/cron_job.sh zingproxy-sync
./scripts/cron_job.sh notifications
./scripts/cron_job.sh daily

# Test API endpoints
curl http://localhost:5000/api/send-expiry-notifications
curl http://localhost:5000/api/send-account-details
```

## 📁 Project Structure

```
vps-manager/
├── auth/                    # Authentication module
├── core/                    # Core functionality
│   ├── api_clients/         # API clients for providers
│   ├── models.py           # Database models
│   ├── manager.py          # Main manager class
│   ├── notifier.py         # Notification system
│   ├── rocket_chat.py      # RocketChat integration
│   └── scheduler.py        # Legacy scheduler (deprecated)
├── ui/                     # Web interface
│   ├── static/            # CSS, JS, images
│   ├── templates/         # HTML templates
│   └── app.py            # Flask application
├── scripts/               # Utility scripts
│   ├── cron_job.sh       # Main cron job script
│   ├── install_cron.sh   # Cron installation
│   └── init_db.py        # Database initialization
├── tests/                 # Test files
├── logs/                  # Log files
├── instance/              # Database files
├── migrations/            # Database migrations
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # Docker image
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the logs in `logs/` directory
3. Check cron job logs: `tail -f logs/cron_job.log`
4. Open an issue on GitHub
5. Contact the development team

## 🎯 Roadmap

- [x] Multi-provider support (BitLaunch, ZingProxy, CloudFly)
- [x] RocketChat notifications
- [x] Cron job system
- [x] Proxy management
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] More provider integrations
- [ ] API rate limiting
- [ ] Advanced backup features
- [ ] Real-time notifications via WebSocket
- [ ] Health monitoring dashboard

## 🙏 Acknowledgments

- Flask team for the excellent web framework
- PostgreSQL team for the robust database
- RocketChat team for the messaging platform
- All contributors and users

---

**Made with ❤️ for VPS management**