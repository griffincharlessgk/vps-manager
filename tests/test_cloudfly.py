import pytest
from unittest.mock import Mock, patch
from core.api_clients.cloudfly import CloudFlyClient, CloudFlyAPIError

@pytest.fixture
def mock_cloudfly_client():
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post, patch('requests.delete') as mock_delete:
        client = CloudFlyClient('test_token')
        yield client

@pytest.fixture
def sample_user_info():
    return {
        'email': 'test@cloudfly.vn',
        'clients': [{
            'wallet': {
                'main_balance': 100000
            }
        }]
    }

@pytest.fixture
def sample_instances():
    return {
        'results': [
            {
                'id': 1,
                'display_name': 'Test VPS 1',
                'status': 'ACTIVE',
                'accessIPv4': '192.168.1.1',
                'region': {'description': 'HN-Cloud01'},
                'flavor': {'description': 'Standard'},
                'image': {'name': 'CentOS-7.9'}
            },
            {
                'id': 2,
                'display_name': 'Test VPS 2',
                'status': 'SHUTOFF',
                'accessIPv4': '192.168.1.2',
                'region': {'description': 'SG-Cloud01'},
                'flavor': {'description': 'Premium'},
                'image': {'name': 'Ubuntu-20.04'}
            }
        ]
    }

def test_cloudfly_client_init():
    client = CloudFlyClient('test_token')
    assert client.api_token == 'test_token'
    assert client.base_url == 'https://api.cloudfly.vn'

def test_get_user_info_success(mock_cloudfly_client, sample_user_info):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_user_info
    
    with patch('requests.get', return_value=mock_response):
        result = mock_cloudfly_client.get_user_info()
        assert result == sample_user_info

def test_get_user_info_error(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = Exception('Unauthorized')
    
    with patch('requests.get', return_value=mock_response):
        with pytest.raises(CloudFlyAPIError, match='Unauthorized'):
            mock_cloudfly_client.get_user_info()

def test_list_instances_success(mock_cloudfly_client, sample_instances):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_instances
    
    with patch('requests.get', return_value=mock_response):
        result = mock_cloudfly_client.list_instances()
        assert len(result) == 2
        assert result[0]['display_name'] == 'Test VPS 1'
        assert result[1]['display_name'] == 'Test VPS 2'

def test_list_instances_empty(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'results': []}
    
    with patch('requests.get', return_value=mock_response):
        result = mock_cloudfly_client.list_instances()
        assert result == []

def test_create_instance_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'id': 3, 'status': 'BUILDING'}
    
    instance_data = {
        'region': 'HN-Cloud01',
        'image_name': 'CentOS-7.9',
        'flavor_type': 'Standard',
        'ram': 1,
        'vcpus': 1,
        'disk': 20
    }
    
    with patch('requests.post', return_value=mock_response):
        result = mock_cloudfly_client.create_instance(instance_data)
        assert result['id'] == 3
        assert result['status'] == 'BUILDING'

def test_delete_instance_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 204
    
    with patch('requests.delete', return_value=mock_response):
        result = mock_cloudfly_client.delete_instance(1)
        assert result is True

def test_delete_instance_error(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = Exception('Not Found')
    
    with patch('requests.delete', return_value=mock_response):
        with pytest.raises(CloudFlyAPIError, match='Not Found'):
            mock_cloudfly_client.delete_instance(999)

def test_start_instance_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'STARTING'}
    
    with patch('requests.post', return_value=mock_response):
        result = mock_cloudfly_client.start_instance(1)
        assert result['status'] == 'STARTING'

def test_stop_instance_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'STOPPING'}
    
    with patch('requests.post', return_value=mock_response):
        result = mock_cloudfly_client.stop_instance(1)
        assert result['status'] == 'STOPPING'

def test_restart_instance_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'REBOOTING'}
    
    with patch('requests.post', return_value=mock_response):
        result = mock_cloudfly_client.restart_instance(1)
        assert result['status'] == 'REBOOTING'

def test_list_regions_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {'id': 'HN-Cloud01', 'description': 'Hanoi Cloud 01'},
        {'id': 'SG-Cloud01', 'description': 'Singapore Cloud 01'}
    ]
    
    with patch('requests.get', return_value=mock_response):
        result = mock_cloudfly_client.list_regions()
        assert len(result) == 2
        assert result[0]['description'] == 'Hanoi Cloud 01'

def test_list_images_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {'id': 'centos-7.9', 'name': 'CentOS-7.9'},
        {'id': 'ubuntu-20.04', 'name': 'Ubuntu-20.04'}
    ]
    
    with patch('requests.get', return_value=mock_response):
        result = mock_cloudfly_client.list_images()
        assert len(result) == 2
        assert result[0]['name'] == 'CentOS-7.9'

def test_list_flavors_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {'id': 'standard', 'description': 'Standard'},
        {'id': 'premium', 'description': 'Premium'}
    ]
    
    with patch('requests.get', return_value=mock_response):
        result = mock_cloudfly_client.list_flavors()
        assert len(result) == 2
        assert result[0]['description'] == 'Standard'

def test_get_billing_info_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'total_usage': 50.0,
        'current_balance': 100000
    }
    
    with patch('requests.get', return_value=mock_response):
        result = mock_cloudfly_client.get_billing_info()
        assert result['total_usage'] == 50.0
        assert result['current_balance'] == 100000

def test_get_usage_stats_success(mock_cloudfly_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'cpu_usage': 25.5,
        'memory_usage': 60.0,
        'disk_usage': 40.0
    }
    
    with patch('requests.get', return_value=mock_response):
        result = mock_cloudfly_client.get_usage_stats(1)
        assert result['cpu_usage'] == 25.5
        assert result['memory_usage'] == 60.0 