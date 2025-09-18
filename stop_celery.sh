#!/bin/bash
# Stop all Celery services

echo "🛑 Stopping Celery services..."

# Kill all celery processes
pkill -f "run_celery_worker.py"
pkill -f "run_celery_beat.py"
pkill -f "run_celery_flower.py"
pkill -f "celery worker"
pkill -f "celery beat"
pkill -f "celery flower"

echo "✅ All Celery services stopped!"
