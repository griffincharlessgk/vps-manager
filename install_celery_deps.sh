#!/bin/bash
# Install Celery dependencies

echo "📦 Installing Celery dependencies..."
echo "===================================="

# Update package list
echo "🔄 Updating package list..."
sudo apt update

# Install Redis
echo "🔄 Installing Redis..."
sudo apt install -y redis-server

# Start Redis service
echo "🔄 Starting Redis service..."
sudo systemctl start redis
sudo systemctl enable redis

# Check Redis status
if systemctl is-active --quiet redis; then
    echo "✅ Redis is running"
else
    echo "❌ Redis failed to start"
    exit 1
fi

# Install Python dependencies
echo "🔄 Installing Python dependencies..."
pip install -r requirements.txt

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Make scripts executable
echo "🔄 Making scripts executable..."
chmod +x start_celery_services.sh
chmod +x stop_celery_services.sh

echo ""
echo "✅ Installation completed!"
echo ""
echo "🚀 To start Celery services:"
echo "   ./start_celery_services.sh"
echo ""
echo "🛑 To stop Celery services:"
echo "   ./stop_celery_services.sh"
echo ""
echo "🧪 To test Celery tasks:"
echo "   python test_celery_tasks.py"
