#!/usr/bin/env python3
"""
Final Celery test
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_celery_final():
    """Final Celery test"""
    print("🚀 Final Celery test...")
    
    try:
        from ui.app import create_app
        from core.celery_app import init_celery
        
        # Create Flask app
        app = create_app()
        
        # Initialize Celery
        with app.app_context():
            celery_app = init_celery(app)
            
            print("✅ Celery initialized")
            
            # Test task
            result = celery_app.send_task('core.tasks.api_tasks.update_bitlaunch_apis')
            print(f"📤 Task sent: {result.id}")
            
            # Check worker
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                print(f"✅ Worker running: {len(stats)} workers")
            else:
                print("❌ No workers")
            
            # Check schedule
            beat_schedule = celery_app.conf.beat_schedule
            print(f"📅 Scheduled tasks: {len(beat_schedule)}")
            
            print("✅ Test completed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_celery_final()
