#!/usr/bin/env python3
"""
Database initialization script
Creates tables and initial admin user
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from ui.app import create_app
from core.models import db, User
from core.logging_config import setup_logging
import logging

def init_database():
    """Initialize database and create admin user"""
    app = create_app()
    
    with app.app_context():
        # Setup logging
        setup_logging(app)
        logger = logging.getLogger(__name__)
        
        try:
            # Create all tables
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                logger.info("Creating admin user...")
                admin_user = User(
                    username='admin',
                    role='admin',
                    notify_days=3,
                    notify_hour=8
                )
                admin_user.set_password('admin123')  # Change this in production!
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Admin user created successfully")
                logger.warning("Default admin password is 'admin123' ")
            else:
                logger.info("Admin user already exists")
            
            # Create logs directory
            log_dir = Path(__file__).parent.parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            logger.info(f"Logs directory created: {log_dir}")
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

if __name__ == '__main__':
    init_database() 