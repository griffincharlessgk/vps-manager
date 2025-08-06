# 🚀 VPS Manager

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
4.  **Generate production keys**
   ```bash
   python scripts/generate_keys.py

   # Edit .env with your configuration
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

7. **Run the application**
   ```bash
    $env:FLASK_APP = "ui.app:create_app" python -m flask run
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


