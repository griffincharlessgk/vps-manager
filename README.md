# 🚀 VPS Manager

A comprehensive VPS and account management system with automated notifications, multi-provider support, and user management.

## ✨ Features

- **Multi-Provider Support**: BitLaunch, ZingProxy
- **Automated Notifications**: Telegram integration with customizable schedules
- **User Management**: Role-based access control with admin/user permissions
- **Data Encryption**: Sensitive data encrypted at rest using Fernet
- **Real-time Monitoring**: Dashboard with expiry warnings and status tracking
- **API Integration**: Direct integration with provider APIs for real-time data
- **Cross-Platform**: Support for Windows, Linux, and macOS

## 🔧 Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: PostgreSQL (production), SQLite (development)
- **Scheduler**: APScheduler
- **Encryption**: Cryptography (Fernet)
- **API Integration**: pybitlaunch, requests
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Deployment**: Docker, Gunicorn

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+ (for production)
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Manager
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

6. **Run the application**
   ```bash
   python -m flask run
   ```

## 📋 Setup for Different Platforms

### Windows Setup
```bash
# Generate production keys
python scripts/generate_keys.py

# Setup PostgreSQL (Windows)
python scripts/setup_postgresql_windows.py

# Initialize database
python scripts/init_db.py

# Run application
python -m flask run
```

### Linux/macOS Setup
```bash
# Generate production keys
python scripts/generate_keys.py

# Setup PostgreSQL
python scripts/setup_postgresql.py

# Initialize database
python scripts/init_db.py

# Run application
python -m flask run
```

## 🔐 Security Features

✅ **Environment Variables**: All sensitive configuration moved to environment variables
✅ **Data Encryption**: API keys, passwords, and tokens encrypted in database
✅ **Input Validation**: Comprehensive validation for all user inputs
✅ **Security Headers**: XSS protection, CSRF protection, and other security headers
✅ **Non-root Docker**: Container runs as non-root user
✅ **Logging**: Structured logging with security event tracking
✅ **Error Handling**: Proper error handling and logging

## 🌐 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | - |
| `DATABASE_URL` | Database connection string | No | `sqlite:///users.db` |
| `TELEGRAM_TOKEN` | Telegram bot token | No | - |
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

### ZingProxy Integration
- `POST /api/zingproxy-login` - Add ZingProxy account
- `GET /api/zingproxy-accounts` - List ZingProxy accounts
- `POST /api/zingproxy-update-proxies/<id>` - Update proxies

### Notifications
- `POST /api/notify-telegram` - Send Telegram notification
- `POST /api/send-all-notifications` - Send to all users
- `GET /api/expiry-warnings` - Get expiry warnings

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

### Health Checks
```bash
curl http://localhost:5000/me
```

## 🔄 Backup and Maintenance

### Database Backup
```bash
# PostgreSQL
pg_dump vps_manager > backup.sql

# SQLite
cp instance/users.db backup.db
```

### Automated Backup (Windows)
```bash
scripts/backup_windows.bat
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check `DATABASE_URL` environment variable
   - Ensure database is running
   - Verify credentials

2. **Encryption Errors**
   - Ensure `ENCRYPTION_KEY` is set
   - Don't change encryption key after data is stored

3. **Telegram Notifications Not Working**
   - Verify `TELEGRAM_TOKEN` is correct
   - Check bot permissions
   - Verify chat IDs

### Debug Mode
```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
python -m flask run
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
3. Open an issue on GitHub
4. Contact the development team

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] More provider integrations
- [ ] API rate limiting
- [ ] Advanced backup features
- [ ] Real-time notifications via WebSocket

## 🙏 Acknowledgments

- Flask team for the excellent web framework
- PostgreSQL team for the robust database
- Telegram team for the messaging API
- All contributors and users

---

**Made with ❤️ for VPS management** 