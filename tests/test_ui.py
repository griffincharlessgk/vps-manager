import pytest
from ui.app import create_app
from core.models import db, User

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Tạo user và login để vượt qua auth
            if not User.query.filter_by(username='apitester').first():
                u = User(username='apitester', role='admin')
                u.set_password('apipass123')
                db.session.add(u)
                db.session.commit()
        client.post('/login', json={'username': 'apitester', 'password': 'apipass123'})
        yield client

def test_list_vps(client):
    rv = client.get('/api/vps')
    assert rv.status_code == 200
    assert isinstance(rv.get_json(), list)

def test_list_accounts(client):
    rv = client.get('/api/accounts')
    assert rv.status_code == 200
    assert isinstance(rv.get_json(), list)

def test_list_expiry_warnings(client):
    rv = client.get('/api/expiry-warnings')
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, dict)
    assert data.get('status') in ['success', 'error']