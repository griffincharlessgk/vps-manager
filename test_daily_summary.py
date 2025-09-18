#!/usr/bin/env python3
"""
Test daily summary task
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import create_app
from core.celery_app import init_celery

def test_daily_summary():
    """Test daily summary task"""
    print("🧪 Testing daily summary task...")
    
    try:
        app = create_app()
        with app.app_context():
            celery_app = init_celery(app)
            
            # Test daily summary task
            print("📤 Sending daily summary task...")
            result = celery_app.send_task('core.tasks.notification_tasks.send_daily_summary')
            print(f"   Task ID: {result.id}")
            print(f"   Status: {result.status}")
            
            # Wait a bit for task to complete
            import time
            time.sleep(3)
            
            print(f"   Final Status: {result.status}")
            if result.status == 'SUCCESS':
                print("✅ Daily summary task completed successfully!")
            else:
                print(f"❌ Daily summary task failed: {result.status}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_daily_summary()
