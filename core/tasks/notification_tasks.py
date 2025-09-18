"""
Celery tasks for notifications
"""

import logging
from datetime import datetime, timedelta
from celery import current_task
from core.celery_app import get_celery
from core import manager, notifier

logger = logging.getLogger(__name__)

# Get Celery instance
celery = get_celery()

@celery.task(bind=True, name='core.tasks.notification_tasks.send_expiry_warnings')
def send_expiry_warnings(self):
    """Send expiry warnings for VPS and accounts"""
    try:
        logger.info("Starting expiry warnings task")
        
        # Get VPS and accounts
        vps_list = manager.list_vps()
        acc_list = manager.list_accounts()
        
        logger.info(f"Found {len(vps_list)} VPS and {len(acc_list)} accounts")
        
        # Send VPS expiry warnings
        vps_warnings_sent = 0
        try:
            notifier.notify_expiry_per_user(vps_list, item_type='VPS', force=False)
            vps_warnings_sent = len([vps for vps in vps_list if vps.get('expiry')])
            logger.info(f"Sent {vps_warnings_sent} VPS expiry warnings")
        except Exception as e:
            logger.error(f"Error sending VPS expiry warnings: {str(e)}")
        
        # Send account expiry warnings
        acc_warnings_sent = 0
        try:
            notifier.notify_expiry_per_user(acc_list, item_type='Account', force=False)
            acc_warnings_sent = len([acc for acc in acc_list if acc.get('expiry')])
            logger.info(f"Sent {acc_warnings_sent} account expiry warnings")
        except Exception as e:
            logger.error(f"Error sending account expiry warnings: {str(e)}")
        
        result = {
            'status': 'completed',
            'vps_warnings': vps_warnings_sent,
            'account_warnings': acc_warnings_sent,
            'total_vps': len(vps_list),
            'total_accounts': len(acc_list)
        }
        
        logger.info(f"Expiry warnings task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Expiry warnings task failed: {str(e)}")
        raise

@celery.task(bind=True, name='core.tasks.notification_tasks.send_daily_summary')
def send_daily_summary(self):
    """Send daily summary notifications"""
    try:
        logger.info("Starting daily summary task")
        
        # Get VPS and accounts
        vps_list = manager.list_vps()
        acc_list = manager.list_accounts()
        
        # Get API information
        bitlaunch_apis = manager.list_bitlaunch_apis()
        zingproxy_apis = manager.list_zingproxy_accounts()
        cloudfly_apis = manager.list_cloudfly_apis()
        
        logger.info(f"Found {len(vps_list)} VPS, {len(acc_list)} accounts")
        logger.info(f"Found {len(bitlaunch_apis)} BitLaunch APIs, {len(zingproxy_apis)} ZingProxy APIs, {len(cloudfly_apis)} CloudFly APIs")
        
        # Send daily summary
        try:
            notifier.send_daily_summary(
                vps_list=vps_list,
                acc_list=acc_list,
                bitlaunch_apis=bitlaunch_apis,
                zingproxy_apis=zingproxy_apis,
                cloudfly_apis=cloudfly_apis
            )
            logger.info("Daily summary sent successfully")
        except Exception as e:
            logger.error(f"Error sending daily summary: {str(e)}")
        
        result = {
            'status': 'completed',
            'vps_count': len(vps_list),
            'account_count': len(acc_list),
            'bitlaunch_apis': len(bitlaunch_apis),
            'zingproxy_apis': len(zingproxy_apis),
            'cloudfly_apis': len(cloudfly_apis)
        }
        
        logger.info(f"Daily summary task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Daily summary task failed: {str(e)}")
        raise

@celery.task(bind=True, name='core.tasks.notification_tasks.send_weekly_report')
def send_weekly_report(self):
    """Send weekly report"""
    try:
        logger.info("Starting weekly report task")
        
        # Get all data for weekly report
        vps_list = manager.list_vps()
        acc_list = manager.list_accounts()
        
        # Get API information
        bitlaunch_apis = manager.list_bitlaunch_apis()
        zingproxy_apis = manager.list_zingproxy_accounts()
        cloudfly_apis = manager.list_cloudfly_apis()
        
        # Calculate weekly statistics
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        # Count expiring items
        expiring_vps = len([vps for vps in vps_list 
                           if vps.get('expiry') and 
                           datetime.strptime(vps['expiry'], '%Y-%m-%d') <= now + timedelta(days=7)])
        
        expiring_accounts = len([acc for acc in acc_list 
                                if acc.get('expiry') and 
                                datetime.strptime(acc['expiry'], '%Y-%m-%d') <= now + timedelta(days=7)])
        
        # Send weekly report
        try:
            notifier.send_weekly_report(
                vps_list=vps_list,
                acc_list=acc_list,
                bitlaunch_apis=bitlaunch_apis,
                zingproxy_apis=zingproxy_apis,
                cloudfly_apis=cloudfly_apis,
                expiring_vps=expiring_vps,
                expiring_accounts=expiring_accounts
            )
            logger.info("Weekly report sent successfully")
        except Exception as e:
            logger.error(f"Error sending weekly report: {str(e)}")
        
        result = {
            'status': 'completed',
            'vps_count': len(vps_list),
            'account_count': len(acc_list),
            'expiring_vps': expiring_vps,
            'expiring_accounts': expiring_accounts,
            'bitlaunch_apis': len(bitlaunch_apis),
            'zingproxy_apis': len(zingproxy_apis),
            'cloudfly_apis': len(cloudfly_apis)
        }
        
        logger.info(f"Weekly report task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Weekly report task failed: {str(e)}")
        raise

@celery.task(bind=True, name='core.tasks.notification_tasks.send_rocketchat_daily_notifications')
def send_rocketchat_daily_notifications(self):
    """Send Rocket.Chat daily notifications"""
    try:
        logger.info("Starting Rocket.Chat daily notifications task")
        
        # Get VPS and accounts
        vps_list = manager.list_vps()
        acc_list = manager.list_accounts()
        
        # Send Rocket.Chat notifications
        try:
            notifier.send_rocketchat_daily_notifications(vps_list, acc_list)
            logger.info("Rocket.Chat daily notifications sent successfully")
        except Exception as e:
            logger.error(f"Error sending Rocket.Chat daily notifications: {str(e)}")
        
        result = {
            'status': 'completed',
            'vps_count': len(vps_list),
            'account_count': len(acc_list)
        }
        
        logger.info(f"Rocket.Chat daily notifications task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Rocket.Chat daily notifications task failed: {str(e)}")
        raise
