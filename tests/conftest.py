import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'True'

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    from ui.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Create tables
    with app.app_context():
        from core.models import db
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(autouse=True)
def app_context(app):
    """Automatically provide app context for all tests."""
    with app.app_context():
        yield

@pytest.fixture(autouse=True)
def client(app):
    """Create a test client for the app."""
    return app.test_client() 