"""
Celery tasks for sync operations
"""

import logging
from datetime import datetime
from celery import current_task
from core.celery_app import get_celery
from core import manager
from core.api_clients.zingproxy import ZingProxyClient

logger = logging.getLogger(__name__)

# Get Celery instance
celery = get_celery()

@celery.task(bind=True, name='core.tasks.sync_tasks.sync_zingproxy_proxies')
def sync_zingproxy_proxies(self):
    """Sync ZingProxy proxies"""
    try:
        logger.info("Starting ZingProxy proxy sync task")
        
        # Get all ZingProxy APIs
        apis = manager.get_zingproxy_apis()
        logger.info(f"Found {len(apis)} ZingProxy APIs for proxy sync")
        
        synced_count = 0
        error_count = 0
        
        for api in apis:
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': synced_count + error_count, 'total': len(apis)}
                )
                
                # Create ZingProxy client
                client = ZingProxyClient(api.api_key)
                
                # Get all active proxies
                proxies = client.get_all_active_proxies()
                if proxies:
                    # Sync proxies to database
                    manager.sync_zingproxy_proxies(api.id, proxies)
                    synced_count += 1
                    logger.info(f"Synced {len(proxies)} proxies for ZingProxy API {api.id}")
                else:
                    error_count += 1
                    logger.warning(f"No proxies found for ZingProxy API {api.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error syncing ZingProxy proxies for API {api.id}: {str(e)}")
        
        result = {
            'status': 'completed',
            'synced': synced_count,
            'errors': error_count,
            'total': len(apis)
        }
        
        logger.info(f"ZingProxy proxy sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"ZingProxy proxy sync task failed: {str(e)}")
        raise

@celery.task(bind=True, name='core.tasks.sync_tasks.auto_sync_zingproxy_proxies')
def auto_sync_zingproxy_proxies(self):
    """Auto sync ZingProxy proxies (scheduled task)"""
    try:
        logger.info("Starting auto ZingProxy proxy sync task")
        
        # Get all active ZingProxy APIs
        apis = manager.get_zingproxy_apis()
        active_apis = [api for api in apis if api.is_active]
        
        logger.info(f"Found {len(active_apis)} active ZingProxy APIs for auto sync")
        
        synced_count = 0
        error_count = 0
        
        for api in active_apis:
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': synced_count + error_count, 'total': len(active_apis)}
                )
                
                # Create ZingProxy client
                client = ZingProxyClient(api.api_key)
                
                # Get all active proxies
                proxies = client.get_all_active_proxies()
                if proxies:
                    # Sync proxies to database
                    manager.sync_zingproxy_proxies(api.id, proxies)
                    synced_count += 1
                    logger.info(f"Auto synced {len(proxies)} proxies for ZingProxy API {api.id}")
                else:
                    error_count += 1
                    logger.warning(f"No proxies found for ZingProxy API {api.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error auto syncing ZingProxy proxies for API {api.id}: {str(e)}")
        
        result = {
            'status': 'completed',
            'synced': synced_count,
            'errors': error_count,
            'total': len(active_apis)
        }
        
        logger.info(f"Auto ZingProxy proxy sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Auto ZingProxy proxy sync task failed: {str(e)}")
        raise
