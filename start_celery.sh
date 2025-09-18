#!/bin/bash
# Start all Celery services

echo "🚀 Starting Celery services..."

# Activate virtual environment
source venv/bin/activate

# Start worker
echo "🔄 Starting Celery worker..."
nohup python run_celery_worker.py > logs/celery_worker.log 2>&1 &
echo "   Worker started"

# Start beat
echo "🔄 Starting Celery Beat..."
nohup python run_celery_beat.py > logs/celery_beat.log 2>&1 &
echo "   Beat started"

# Start flower
echo "🔄 Starting Flower..."
nohup python run_celery_flower.py > logs/celery_flower.log 2>&1 &
echo "   Flower started"

echo "✅ All Celery services started!"
echo "🌐 Flower: http://localhost:5555"
