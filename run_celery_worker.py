#!/usr/bin/env python3
"""
Run Celery worker
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import create_app
from core.celery_app import init_celery

# Create Flask app
app = create_app()

# Initialize Celery with Flask app context
with app.app_context():
    celery_app = init_celery(app)

if __name__ == '__main__':
    # Start Celery worker
    celery_app.worker_main(['worker', '--loglevel=info'])
