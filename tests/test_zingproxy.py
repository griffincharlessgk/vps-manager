import pytest
from unittest.mock import patch, Mock
from core.api_clients.zingproxy import ZingProxyClient, ZingProxyAPIError

EMAIL = 'test@example.com'
PASSWORD = 'password123'
TOKEN = 'testtoken'

@pytest.fixture
def mock_post():
    with patch('requests.post') as mock:
        yield mock

@pytest.fixture
def mock_get():
    with patch('requests.get') as mock:
        yield mock

def test_login_success(mock_post):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'status': 'success', 'accessToken': TOKEN}
    mock_post.return_value = mock_resp
    client = ZingProxyClient(EMAIL, PASSWORD)
    assert client.access_token == TOKEN

def test_login_fail(mock_post):
    mock_resp = Mock()
    mock_resp.status_code = 401
    mock_resp.text = 'Unauthorized'
    mock_resp.json.return_value = {'status': 'error'}
    mock_post.return_value = mock_resp
    with pytest.raises(ZingProxyAPIError):
        ZingProxyClient(EMAIL, PASSWORD)

def test_get_account_details_success(mock_post, mock_get):
    # login
    mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success', 'accessToken': TOKEN})
    # get details
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        'status': 'success',
        'user': {
            'email': EMAIL,
            'balance': 123456,
            'fullname': 'Test User',
            'customerId': 'ZP123',
        }
    }
    mock_get.return_value = mock_resp
    client = ZingProxyClient(EMAIL, PASSWORD)
    user = client.get_account_details()
    assert user['email'] == EMAIL
    assert user['balance'] == 123456
    assert user['customerId'] == 'ZP123'

def test_get_account_details_fail(mock_post, mock_get):
    mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success', 'accessToken': TOKEN})
    mock_resp = Mock()
    mock_resp.status_code = 403
    mock_resp.text = 'Forbidden'
    mock_resp.json.return_value = {'status': 'error'}
    mock_get.return_value = mock_resp
    client = ZingProxyClient(EMAIL, PASSWORD)
    with pytest.raises(ZingProxyAPIError):
        client.get_account_details()

def test_get_all_active_proxies_success(mock_post, mock_get):
    mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success', 'accessToken': TOKEN})
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'data': [{'proxy_id': '1', 'ip': '1.2.3.4'}]}
    mock_get.return_value = mock_resp
    client = ZingProxyClient(EMAIL, PASSWORD)
    proxies = client.get_all_active_proxies()
    assert isinstance(proxies, list)
    assert proxies[0]['proxy_id'] == '1'

def test_get_proxies_by_status_success(mock_post, mock_get):
    mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success', 'accessToken': TOKEN})
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'data': [{'proxy_id': '2', 'status': 'running'}]}
    mock_get.return_value = mock_resp
    client = ZingProxyClient(EMAIL, PASSWORD)
    proxies = client.get_proxies_by_status('running')
    assert proxies[0]['status'] == 'running' 