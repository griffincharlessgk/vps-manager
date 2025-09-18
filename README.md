# 🚀 VPS Manager

A comprehensive VPS and account management system with automated notifications, multi-provider support, and user management powered by Celery for scalable task processing.

## ✨ Features

- **Multi-Provider Support**: BitLaunch, ZingProxy, CloudFly
- **Automated Notifications**: Rocket.Chat integration with customizable schedules
- **User Management**: Role-based access control with admin/user permissions
- **Data Encryption**: Sensitive data encrypted at rest using Fernet
- **Real-time Monitoring**: Dashboard with expiry warnings and status tracking
- **API Integration**: Direct integration with provider APIs for real-time data
- **Scalable Task Processing**: Celery-based background task processing
- **Cross-Platform**: Support for Windows, Linux, and macOS

## 🔧 Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: PostgreSQL (production), SQLite (development)
- **Task Queue**: Celery with Redis
- **Scheduler**: Celery Beat
- **Monitoring**: Flower (Celery monitoring)
- **Encryption**: Cryptography (Fernet)
- **API Integration**: pybitlaunch, requests
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Deployment**: Docker, Gunicorn

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis server
- PostgreSQL 12+ (for production)
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
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Celery dependencies**
   ```bash
   ./install_celery_deps.sh
   ```

5. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

6. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

## 🏃‍♂️ Running the Application

### 1. Start Celery Services

```bash
# Start all Celery services (worker, beat, flower)
./start_celery.sh

# Or start individually:
python run_celery_worker.py &
python run_celery_beat.py &
python run_celery_flower.py &
```

### 2. Start Flask Application

```bash
# Method 1: Run from ui directory (Recommended)
cd ui
python -m flask run

# Method 2: Run from root directory with FLASK_APP
export FLASK_APP=ui.app
python -m flask run

# Method 3: Run directly with Python
cd ui
python app.py

# Method 4: Use --app flag from root directory
python -m flask --app ui.app run
```

### 3. Access the Application

- **Web Application**: http://localhost:5000
- **Flower Monitoring**: http://localhost:5555

## 🔄 Celery Task Management

### Scheduled Tasks

The system runs the following automated tasks:

- **API Updates** (Daily):
  - BitLaunch: 6:00 AM, 6:30 AM
  - ZingProxy: 7:00 AM
  - CloudFly: 8:00 AM, 8:30 AM

- **Notifications** (Every 5 minutes):
  - Expiry warnings
  - Daily summary

- **Sync Tasks**:
  - ZingProxy proxies: Every 2 hours
  - Auto sync: 2:00 AM daily

- **Reports**:
  - Weekly report: Monday, 10:00 AM
  - Rocket.Chat: 11:07 AM daily

### Managing Celery Services

```bash
# Start all services
./start_celery.sh

# Stop all services
./stop_celery.sh

# Test Celery tasks
python test_celery_final.py

# View logs
tail -f logs/celery_worker.log
tail -f logs/celery_beat.log
tail -f logs/celery_flower.log
```

## 🔐 Security Features

✅ **Environment Variables**: All sensitive configuration moved to environment variables
✅ **Data Encryption**: API keys, passwords, and tokens encrypted in database
✅ **Input Validation**: Comprehensive validation for all user inputs
✅ **Security Headers**: XSS protection, CSRF protection, and other security headers
✅ **Non-root Docker**: Container runs as non-root user
✅ **Logging**: Structured logging with security event tracking
✅ **Error Handling**: Proper error handling and logging
✅ **Task Security**: Celery tasks run in isolated processes

## 🌐 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | - |
| `DATABASE_URL` | Database connection string | No | `sqlite:///users.db` |
| `CELERY_BROKER_URL` | Redis broker URL | No | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis result backend | No | `redis://localhost:6379/0` |
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
- `rocket_chat_configs`: Rocket.Chat notification settings

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

### Provider Integrations
- **BitLaunch**: `/api/bitlaunch-*` endpoints
- **ZingProxy**: `/api/zingproxy-*` endpoints
- **CloudFly**: `/api/cloudfly-*` endpoints

### Notifications
- `POST /api/send-all-notifications` - Send to all users
- `GET /api/expiry-warnings` - Get expiry warnings
- `POST /api/send-detailed-info` - Send detailed account info

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
- `logs/celery_worker.log` - Celery worker logs
- `logs/celery_beat.log` - Celery beat logs
- `logs/celery_flower.log` - Flower logs

### Health Checks
```bash
# Flask app
curl http://localhost:5000/me

# Celery worker
celery -A core.celery_app.celery_app inspect active

# Redis
redis-cli ping
```

### Flower Monitoring
Access Flower at http://localhost:5555 to monitor:
- Active tasks
- Task history
- Worker status
- Scheduled tasks
- Task results

## 🔄 Backup and Maintenance

### Database Backup
```bash
# PostgreSQL
pg_dump vps_manager > backup.sql

# SQLite
cp instance/users.db backup.db
```

### Celery Task Monitoring
```bash
# Check worker status
celery -A core.celery_app.celery_app inspect stats

# Check scheduled tasks
celery -A core.celery_app.celery_app inspect scheduled

# Purge all tasks
celery -A core.celery_app.celery_app purge
```

## 🚨 Troubleshooting

### Common Issues

1. **Flask Application Not Found**
   - Make sure you're in the correct directory (`ui/` folder)
   - Use `export FLASK_APP=ui.app` when running from root directory
   - Or use `python -m flask --app ui.app run` from root directory

2. **Celery Tasks Not Running**
   - Ensure Redis is running: `sudo systemctl status redis-server`
   - Check Celery worker is running: `ps aux | grep celery`
   - Verify Celery Beat is running: `ps aux | grep beat`
   - Check logs: `tail -f logs/celery_worker.log`

3. **Database Connection Errors**
   - Check `DATABASE_URL` environment variable
   - Ensure database is running
   - Verify credentials

4. **Redis Connection Errors**
   - Ensure Redis server is running
   - Check `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`
   - Verify Redis is accessible

5. **Encryption Errors**
   - Ensure `ENCRYPTION_KEY` is set
   - Don't change encryption key after data is stored

### Debug Mode
```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
cd ui
python -m flask run
```

### Celery Debug
```bash
# Run worker in debug mode
celery -A core.celery_app.celery_app worker --loglevel=debug

# Check task results
celery -A core.celery_app.celery_app result <task_id>
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │    │   Celery Beat   │    │  Celery Worker  │
│   (Web UI)      │    │   (Scheduler)   │    │  (Task Exec)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │  (Message Queue)│
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (Database)    │
                    └─────────────────┘
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
3. Check Celery monitoring at http://localhost:5555
4. Open an issue on GitHub
5. Contact the development team

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] More provider integrations
- [ ] API rate limiting
- [ ] Advanced backup features
- [ ] Real-time notifications via WebSocket
- [ ] Celery task prioritization
- [ ] Distributed task processing
- [ ] Task retry policies

## 🙏 Acknowledgments

- Flask team for the excellent web framework
- Celery team for the robust task queue system
- Redis team for the fast in-memory database
- PostgreSQL team for the robust database
- Rocket.Chat team for the messaging platform
- All contributors and users

---

**Made with ❤️ for VPS management**