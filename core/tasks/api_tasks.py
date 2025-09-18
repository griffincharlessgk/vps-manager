"""
Celery tasks for API updates
"""

import logging
from datetime import datetime
from celery import current_task
from core.celery_app import get_celery
from core import manager
from core.api_clients.bitlaunch import BitLaunchClient
from core.api_clients.zingproxy import ZingProxyClient
from core.api_clients.cloudfly import CloudFlyClient

logger = logging.getLogger(__name__)

# Get Celery instance
celery = get_celery()

@celery.task(bind=True, name='core.tasks.api_tasks.update_bitlaunch_apis')
def update_bitlaunch_apis(self):
    """Update BitLaunch API information"""
    try:
        logger.info("Starting BitLaunch API update task")
        
        # Get all BitLaunch APIs
        apis = manager.get_bitlaunch_apis_needing_update()
        logger.info(f"Found {len(apis)} BitLaunch APIs to update")
        
        updated_count = 0
        error_count = 0
        
        for api in apis:
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': updated_count + error_count, 'total': len(apis)}
                )
                
                # Create BitLaunch client
                client = BitLaunchClient(api.api_key)
                
                # Get account info
                account_info = client.get_account_info()
                if account_info:
                    # Update API with new balance
                    manager.update_bitlaunch_api_balance(api.id, account_info.get('balanceUSD', 0))
                    updated_count += 1
                    logger.info(f"Updated BitLaunch API {api.id} with balance {account_info.get('balanceUSD', 0)}")
                else:
                    error_count += 1
                    logger.warning(f"Failed to get account info for BitLaunch API {api.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error updating BitLaunch API {api.id}: {str(e)}")
        
        result = {
            'status': 'completed',
            'updated': updated_count,
            'errors': error_count,
            'total': len(apis)
        }
        
        logger.info(f"BitLaunch API update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"BitLaunch API update task failed: {str(e)}")
        raise

@celery.task(bind=True, name='core.tasks.api_tasks.update_bitlaunch_vps')
def update_bitlaunch_vps(self):
    """Update BitLaunch VPS information"""
    try:
        logger.info("Starting BitLaunch VPS update task")
        
        # Get all BitLaunch APIs
        apis = manager.get_bitlaunch_apis_needing_update()
        logger.info(f"Found {len(apis)} BitLaunch APIs for VPS update")
        
        updated_count = 0
        error_count = 0
        
        for api in apis:
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': updated_count + error_count, 'total': len(apis)}
                )
                
                # Create BitLaunch client
                client = BitLaunchClient(api.api_key)
                
                # Get servers
                servers = client.list_servers()
                if servers:
                    # Update VPS information
                    for server in servers:
                        manager.update_bitlaunch_vps(api.id, server)
                    updated_count += 1
                    logger.info(f"Updated BitLaunch VPS for API {api.id}")
                else:
                    error_count += 1
                    logger.warning(f"No servers found for BitLaunch API {api.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error updating BitLaunch VPS for API {api.id}: {str(e)}")
        
        result = {
            'status': 'completed',
            'updated': updated_count,
            'errors': error_count,
            'total': len(apis)
        }
        
        logger.info(f"BitLaunch VPS update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"BitLaunch VPS update task failed: {str(e)}")
        raise

@celery.task(bind=True, name='core.tasks.api_tasks.update_zingproxy_apis')
def update_zingproxy_apis(self):
    """Update ZingProxy API information"""
    try:
        logger.info("Starting ZingProxy API update task")
        
        # Get all ZingProxy APIs
        apis = manager.get_zingproxy_apis_needing_update()
        logger.info(f"Found {len(apis)} ZingProxy APIs to update")
        
        updated_count = 0
        error_count = 0
        
        for api in apis:
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': updated_count + error_count, 'total': len(apis)}
                )
                
                # Create ZingProxy client
                client = ZingProxyClient(api.api_key)
                
                # Get account details
                account_details = client.get_account_details()
                if account_details:
                    # Update API with new balance
                    manager.update_zingproxy_api_balance(api.id, account_details.get('balance', 0))
                    updated_count += 1
                    logger.info(f"Updated ZingProxy API {api.id} with balance {account_details.get('balance', 0)}")
                else:
                    error_count += 1
                    logger.warning(f"Failed to get account details for ZingProxy API {api.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error updating ZingProxy API {api.id}: {str(e)}")
        
        result = {
            'status': 'completed',
            'updated': updated_count,
            'errors': error_count,
            'total': len(apis)
        }
        
        logger.info(f"ZingProxy API update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"ZingProxy API update task failed: {str(e)}")
        raise

@celery.task(bind=True, name='core.tasks.api_tasks.update_cloudfly_apis')
def update_cloudfly_apis(self):
    """Update CloudFly API information"""
    try:
        logger.info("Starting CloudFly API update task")
        
        # Get all CloudFly APIs
        apis = manager.get_cloudfly_apis_needing_update()
        logger.info(f"Found {len(apis)} CloudFly APIs to update")
        
        updated_count = 0
        error_count = 0
        
        for api in apis:
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': updated_count + error_count, 'total': len(apis)}
                )
                
                # Create CloudFly client
                client = CloudFlyClient(api.api_key)
                
                # Get user info
                user_info = client.get_user_info()
                if user_info:
                    # Update API with new balance
                    balance = 0
                    if 'clients' in user_info and user_info['clients']:
                        balance = user_info['clients'][0].get('wallet', {}).get('main_balance', 0)
                    
                    manager.update_cloudfly_api_balance(api.id, balance)
                    updated_count += 1
                    logger.info(f"Updated CloudFly API {api.id} with balance {balance}")
                else:
                    error_count += 1
                    logger.warning(f"Failed to get user info for CloudFly API {api.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error updating CloudFly API {api.id}: {str(e)}")
        
        result = {
            'status': 'completed',
            'updated': updated_count,
            'errors': error_count,
            'total': len(apis)
        }
        
        logger.info(f"CloudFly API update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"CloudFly API update task failed: {str(e)}")
        raise

@celery.task(bind=True, name='core.tasks.api_tasks.update_cloudfly_vps')
def update_cloudfly_vps(self):
    """Update CloudFly VPS information"""
    try:
        logger.info("Starting CloudFly VPS update task")
        
        # Get all CloudFly APIs
        apis = manager.get_cloudfly_apis_needing_update()
        logger.info(f"Found {len(apis)} CloudFly APIs for VPS update")
        
        updated_count = 0
        error_count = 0
        
        for api in apis:
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': updated_count + error_count, 'total': len(apis)}
                )
                
                # Create CloudFly client
                client = CloudFlyClient(api.api_key)
                
                # Get instances
                instances = client.list_instances()
                if instances:
                    # Update VPS information
                    for instance in instances:
                        manager.update_cloudfly_vps(api.id, instance)
                    updated_count += 1
                    logger.info(f"Updated CloudFly VPS for API {api.id}")
                else:
                    error_count += 1
                    logger.warning(f"No instances found for CloudFly API {api.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error updating CloudFly VPS for API {api.id}: {str(e)}")
        
        result = {
            'status': 'completed',
            'updated': updated_count,
            'errors': error_count,
            'total': len(apis)
        }
        
        logger.info(f"CloudFly VPS update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"CloudFly VPS update task failed: {str(e)}")
        raise
