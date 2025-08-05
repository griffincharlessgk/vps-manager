import pytest
from ui.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
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
    assert isinstance(data, list) 