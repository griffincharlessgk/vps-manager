import pytest
from unittest.mock import Mock, patch
from core.api_clients.bitlaunch import BitLaunchClient, BitLaunchAPIError

@pytest.fixture
def mock_bitlaunch_client():
    with patch('pybitlaunch.Client') as mock_client:
        client = BitLaunchClient('test_token')
        yield client

def test_bitlaunch_client_init():
    with patch('pybitlaunch.Client') as mock_client:
        client = BitLaunchClient('test_token')
        mock_client.assert_called_once_with('test_token')

def test_get_account_info(mock_bitlaunch_client):
    mock_account = {'id': 1, 'email': 'test@example.com', 'balance': 100}
    mock_bitlaunch_client.client.Account.Show.return_value = mock_account
    
    result = mock_bitlaunch_client.get_account_info()
    assert result == mock_account

def test_get_account_usage(mock_bitlaunch_client):
    mock_usage = {'month': '2024-01', 'total': 50}
    mock_bitlaunch_client.client.Account.Usage.return_value = mock_usage
    
    result = mock_bitlaunch_client.get_account_usage('2024-01')
    assert result == mock_usage

def test_get_account_history(mock_bitlaunch_client):
    mock_history = [{'id': 1, 'amount': 10}, {'id': 2, 'amount': 20}]
    mock_bitlaunch_client.client.Account.History.return_value = mock_history
    
    result = mock_bitlaunch_client.get_account_history(1, 25)
    assert result == mock_history

def test_list_servers_success(mock_bitlaunch_client):
    mock_servers = [{'id': 1, 'name': 'server1'}, {'id': 2, 'name': 'server2'}]
    mock_bitlaunch_client.client.Servers.List.return_value = (mock_servers, None)
    
    result = mock_bitlaunch_client.list_servers()
    assert result == mock_servers

def test_list_servers_error(mock_bitlaunch_client):
    mock_bitlaunch_client.client.Servers.List.return_value = (None, 'API Error')
    
    with pytest.raises(BitLaunchAPIError, match='API Error'):
        mock_bitlaunch_client.list_servers()

def test_create_server_success(mock_bitlaunch_client):
    mock_server = {'id': 1, 'name': 'new_server'}
    mock_bitlaunch_client.client.Servers.Create.return_value = (mock_server, None)
    
    result = mock_bitlaunch_client.create_server(name='new_server', hostID=1)
    assert result == mock_server

def test_create_server_error(mock_bitlaunch_client):
    mock_bitlaunch_client.client.Servers.Create.return_value = (None, 'Creation failed')
    
    with pytest.raises(BitLaunchAPIError, match='Creation failed'):
        mock_bitlaunch_client.create_server(name='new_server')

def test_destroy_server_success(mock_bitlaunch_client):
    mock_bitlaunch_client.client.Servers.Destroy.return_value = None
    
    result = mock_bitlaunch_client.destroy_server(1)
    assert result is True

def test_destroy_server_error(mock_bitlaunch_client):
    mock_bitlaunch_client.client.Servers.Destroy.return_value = 'Destroy failed'
    
    with pytest.raises(BitLaunchAPIError, match='Destroy failed'):
        mock_bitlaunch_client.destroy_server(1)

def test_list_ssh_keys(mock_bitlaunch_client):
    mock_keys = [{'id': 1, 'name': 'key1'}, {'id': 2, 'name': 'key2'}]
    mock_bitlaunch_client.client.SSHKeys.List.return_value = mock_keys
    
    result = mock_bitlaunch_client.list_ssh_keys()
    assert result == mock_keys

def test_create_ssh_key_success(mock_bitlaunch_client):
    mock_key = {'id': 1, 'name': 'new_key'}
    mock_bitlaunch_client.client.SSHKeys.Create.return_value = (mock_key, None)
    
    result = mock_bitlaunch_client.create_ssh_key('new_key', 'ssh-rsa...')
    assert result == mock_key

def test_create_ssh_key_error(mock_bitlaunch_client):
    mock_bitlaunch_client.client.SSHKeys.Create.return_value = (None, 'Key creation failed')
    
    with pytest.raises(BitLaunchAPIError, match='Key creation failed'):
        mock_bitlaunch_client.create_ssh_key('new_key', 'ssh-rsa...')

def test_delete_ssh_key_success(mock_bitlaunch_client):
    mock_bitlaunch_client.client.SSHKeys.Delete.return_value = None
    
    result = mock_bitlaunch_client.delete_ssh_key(1)
    assert result is True

def test_delete_ssh_key_error(mock_bitlaunch_client):
    mock_bitlaunch_client.client.SSHKeys.Delete.return_value = 'Delete failed'
    
    with pytest.raises(BitLaunchAPIError, match='Delete failed'):
        mock_bitlaunch_client.delete_ssh_key(1)

def test_list_transactions_success(mock_bitlaunch_client):
    mock_transactions = [{'id': 1, 'amount': 10}, {'id': 2, 'amount': 20}]
    mock_bitlaunch_client.client.Transactions.List.return_value = (mock_transactions, None)
    
    result = mock_bitlaunch_client.list_transactions(1, 25)
    assert result == mock_transactions

def test_list_transactions_error(mock_bitlaunch_client):
    mock_bitlaunch_client.client.Transactions.List.return_value = (None, 'List failed')
    
    with pytest.raises(BitLaunchAPIError, match='List failed'):
        mock_bitlaunch_client.list_transactions()

def test_create_transaction_success(mock_bitlaunch_client):
    mock_transaction = {'id': 1, 'amountUSD': 50}
    mock_bitlaunch_client.client.Transactions.Create.return_value = (mock_transaction, None)
    
    result = mock_bitlaunch_client.create_transaction(50, 'BTC')
    assert result == mock_transaction

def test_create_transaction_error(mock_bitlaunch_client):
    mock_bitlaunch_client.client.Transactions.Create.return_value = (None, 'Transaction failed')
    
    with pytest.raises(BitLaunchAPIError, match='Transaction failed'):
        mock_bitlaunch_client.create_transaction(50)

def test_get_transaction_success(mock_bitlaunch_client):
    mock_transaction = {'id': 1, 'amountUSD': 50, 'status': 'completed'}
    mock_bitlaunch_client.client.Transactions.Show.return_value = (mock_transaction, None)
    
    result = mock_bitlaunch_client.get_transaction(1)
    assert result == mock_transaction

def test_get_transaction_error(mock_bitlaunch_client):
    mock_bitlaunch_client.client.Transactions.Show.return_value = (None, 'Transaction not found')
    
    with pytest.raises(BitLaunchAPIError, match='Transaction not found'):
        mock_bitlaunch_client.get_transaction(1) 