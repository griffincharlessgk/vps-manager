import pytest
from unittest.mock import Mock, patch
from core.rocket_chat import (
    RocketChatClient, 
    send_account_expiry_notification,
    send_daily_account_summary,
    send_detailed_account_info
)

@pytest.fixture
def sample_accounts():
    return [
        {
            'id': 'acc1',
            'username': 'user1@example.com',
            'service': 'BitLaunch',
            'expiry': '2024-12-31',
            'balance': 5000,
            'source': 'bitlaunch'
        },
        {
            'id': 'acc2',
            'username': 'user2@example.com',
            'service': 'ZingProxy',
            'expiry': '2024-11-30',
            'balance': 50000,
            'source': 'zingproxy'
        },
        {
            'id': 'acc3',
            'username': 'user3@example.com',
            'service': 'CloudFly',
            'expiry': '2024-10-31',
            'balance': 25000,
            'source': 'cloudfly'
        }
    ]

@pytest.fixture
def mock_rocket_chat_client():
    with patch('requests.post') as mock_post:
        client = RocketChatClient('test_token', 'test_user_id')
        yield client

def test_rocket_chat_client_init():
    client = RocketChatClient('test_token', 'test_user_id')
    assert client.auth_token == 'test_token'
    assert client.user_id == 'test_user_id'
    assert client.base_url == 'https://rocket.int.team'

@patch('requests.post')
def test_send_message_success(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'success': True}
    mock_post.return_value = mock_response
    
    client = RocketChatClient('test_token', 'test_user_id')
    result = client.send_message('test_room', 'Test message')
    assert isinstance(result, dict)
    assert result.get('success') is True

@patch('requests.post')
def test_send_message_error(mock_post):
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = Exception('Unauthorized')
    mock_post.return_value = mock_response
    
    client = RocketChatClient('test_token', 'test_user_id')
    with pytest.raises(Exception):
        client.send_message('test_room', 'Test message')

@patch('requests.post')
def test_send_formatted_message_success(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'success': True}
    mock_post.return_value = mock_response
    
    client = RocketChatClient('test_token', 'test_user_id')
    result = client.send_formatted_message(
        'test_room', 
        'Test Title', 
        'Test Text', 
        'good'
    )
    assert isinstance(result, dict)
    assert result.get('success') is True

@patch('requests.get')
def test_get_channels_success(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'channels': [
            {'_id': 'ch1', 'name': 'general'},
            {'_id': 'ch2', 'name': 'test'}
        ]
    }
    mock_get.return_value = mock_response
    
    client = RocketChatClient('test_token', 'test_user_id')
    result = client.get_channels()
    assert len(result) == 2
    assert result[0]['name'] == 'general'

@patch('requests.get')
def test_get_groups_success(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'groups': [
            {'_id': 'g1', 'name': 'admin'},
            {'_id': 'g2', 'name': 'support'}
        ]
    }
    mock_get.return_value = mock_response
    
    client = RocketChatClient('test_token', 'test_user_id')
    result = client.get_groups()
    assert len(result) == 2
    assert result[0]['name'] == 'admin'

@patch('core.rocket_chat.RocketChatClient')
def test_send_account_expiry_notification_success(mock_client_class):
    mock_client = Mock()
    mock_client.send_formatted_message.return_value = True
    mock_client_class.return_value = mock_client
    
    result = send_account_expiry_notification(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=[],
        warning_days=7
    )
    assert result is True

@patch('core.rocket_chat.RocketChatClient')
def test_send_account_expiry_notification_with_expiring_accounts(mock_client_class):
    mock_client = Mock()
    mock_client.send_formatted_message.return_value = True
    mock_client_class.return_value = mock_client
    
    # Account sắp hết hạn trong 3 ngày
    expiring_accounts = [
        {
            'id': 'acc1',
            'username': 'user1@example.com',
            'service': 'Test Service',
            'expiry': '2024-12-16',  # 3 ngày nữa
            'source': 'manual'
        }
    ]
    
    result = send_account_expiry_notification(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=expiring_accounts,
        warning_days=7
    )
    assert result is True
    mock_client.send_formatted_message.assert_called_once()

@patch('core.rocket_chat.RocketChatClient')
def test_send_daily_account_summary_success(mock_client_class):
    mock_client = Mock()
    mock_client.send_formatted_message.return_value = True
    mock_client_class.return_value = mock_client
    
    result = send_daily_account_summary(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=[]
    )
    assert result is True

@patch('core.rocket_chat.RocketChatClient')
def test_send_daily_account_summary_with_accounts(mock_client_class):
    mock_client = Mock()
    mock_client.send_formatted_message.return_value = True
    mock_client_class.return_value = mock_client
    
    result = send_daily_account_summary(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=[
            {
                'id': 'acc1',
                'username': 'user1@example.com',
                'service': 'BitLaunch',
                'balance': 10000,
                'source': 'bitlaunch'
            }
        ]
    )
    assert result is True
    mock_client.send_formatted_message.assert_called_once()

@patch('core.rocket_chat.RocketChatClient')
def test_send_detailed_account_info_success(mock_client_class):
    mock_client = Mock()
    mock_client.send_formatted_message.return_value = True
    mock_client_class.return_value = mock_client
    
    result = send_detailed_account_info(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=[]
    )
    assert result is True

@patch('core.rocket_chat.RocketChatClient')
def test_send_detailed_account_info_with_accounts(mock_client_class):
    mock_client = Mock()
    mock_client.send_formatted_message.return_value = True
    mock_client_class.return_value = mock_client
    
    result = send_detailed_account_info(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=[
            {
                'id': 'acc1',
                'username': 'user1@example.com',
                'service': 'BitLaunch',
                'balance': 10000,
                'source': 'bitlaunch'
            }
        ]
    )
    assert result is True
    mock_client.send_formatted_message.assert_called_once()

def test_send_account_expiry_notification_no_accounts():
    result = send_account_expiry_notification(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=[],
        warning_days=7
    )
    assert result is True

def test_send_daily_account_summary_no_accounts():
    result = send_daily_account_summary(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=[]
    )
    assert result is True

def test_send_detailed_account_info_no_accounts():
    result = send_detailed_account_info(
        room_id='test_room',
        auth_token='test_token',
        user_id='test_user',
        accounts=[]
    )
    assert result is True 