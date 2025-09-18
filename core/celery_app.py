"""
Celery configuration and app setup
"""

import os
from celery import Celery
from celery.schedules import crontab
from flask import Flask

def make_celery(app: Flask = None) -> Celery:
    """Create Celery instance with Flask app context"""
    
    # Get Redis URL from environment
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    celery = Celery(
        app.import_name if app else 'vps_manager',
        broker=redis_url,
        backend=redis_url,
        include=[
            'core.tasks.api_tasks',
            'core.tasks.notification_tasks',
            'core.tasks.sync_tasks'
        ]
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        result_expires=3600,  # 1 hour
        task_always_eager=False,  # Set to True for testing
        task_eager_propagates=True,
        task_ignore_result=False,
        task_store_eager_result=True,
        task_acks_late=True,
        worker_disable_rate_limits=False,
        worker_hijack_root_logger=False,
        worker_log_color=False,
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    )
    
    # Configure Celery Beat schedule
    celery.conf.beat_schedule = {
        # API Update Tasks - Daily
        'bitlaunch-daily-update': {
            'task': 'core.tasks.api_tasks.update_bitlaunch_apis',
            'schedule': crontab(hour=6, minute=0),  # 6:00 AM daily
        },
        'bitlaunch-vps-daily-update': {
            'task': 'core.tasks.api_tasks.update_bitlaunch_vps',
            'schedule': crontab(hour=6, minute=30),  # 6:30 AM daily
        },
        'zingproxy-daily-update': {
            'task': 'core.tasks.api_tasks.update_zingproxy_apis',
            'schedule': crontab(hour=7, minute=0),  # 7:00 AM daily
        },
        'cloudfly-daily-update': {
            'task': 'core.tasks.api_tasks.update_cloudfly_apis',
            'schedule': crontab(hour=8, minute=0),  # 8:00 AM daily
        },
        'cloudfly-vps-daily-update': {
            'task': 'core.tasks.api_tasks.update_cloudfly_vps',
            'schedule': crontab(hour=8, minute=30),  # 8:30 AM daily
        },
        
        # Proxy Sync Tasks
        'zingproxy-proxy-sync-daily': {
            'task': 'core.tasks.sync_tasks.sync_zingproxy_proxies',
            'schedule': crontab(hour=8, minute=0),  # 8:00 AM daily
        },
        'zingproxy-proxy-sync-interval': {
            'task': 'core.tasks.sync_tasks.sync_zingproxy_proxies',
            'schedule': crontab(minute='*/120'),  # Every 2 hours
        },
        
        # Notification Tasks - Every 5 minutes
        'expiry-warnings': {
            'task': 'core.tasks.notification_tasks.send_expiry_warnings',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
        'daily-summary': {
            'task': 'core.tasks.notification_tasks.send_daily_summary',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
        
        # Weekly Report
        'weekly-report': {
            'task': 'core.tasks.notification_tasks.send_weekly_report',
            'schedule': crontab(hour=10, minute=0, day_of_week=1),  # Monday 10:00 AM
        },
        
        # Auto sync tasks
        'auto-sync-zingproxy-proxies': {
            'task': 'core.tasks.sync_tasks.auto_sync_zingproxy_proxies',
            'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
        },
        
        # Rocket.Chat daily notifications
        'rocketchat-daily-notifications': {
            'task': 'core.tasks.notification_tasks.send_rocketchat_daily_notifications',
            'schedule': crontab(hour=11, minute=7),  # 11:07 AM daily
        },
    }
    
    # Set timezone
    celery.conf.timezone = 'UTC'
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            if app:
                with app.app_context():
                    return self.run(*args, **kwargs)
            else:
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    return celery

# Create global celery instance
celery_app = None

def init_celery(app: Flask) -> Celery:
    """Initialize Celery with Flask app"""
    global celery_app
    celery_app = make_celery(app)
    return celery_app

def get_celery() -> Celery:
    """Get global Celery instance"""
    global celery_app
    if celery_app is None:
        raise RuntimeError("Celery not initialized. Call init_celery() first.")
    return celery_app
