import pybitlaunch

class BitLaunchAPIError(Exception):
    pass

class BitLaunchClient:
    def __init__(self, token: str):
        self.client = pybitlaunch.Client(token)

    def get_account_info(self):
        """
        Lấy thông tin tài khoản BitLaunch.
        
        Lưu ý: API trả về balance và limit theo đơn vị MILLI-DOLLARS (1/1000 dollar)
        Ví dụ: 1063 = $1.063
        Cần chia cho 1000 để chuyển sang đơn vị dollars khi sử dụng.
        """
        return self.client.Account.Show()

    def get_account_usage(self, month=None):
        if month is None:
            from datetime import datetime
            month = datetime.now().strftime("%Y-%m")
        return self.client.Account.Usage(month)

    def get_account_history(self, page=1, pPage=25):
        history = self.client.Account.History(page, pPage)
        return history

    def list_servers(self):
        servers, err = self.client.Servers.List()
        if err:
            raise BitLaunchAPIError(err)
        return servers

    def create_server(self, **kwargs):
        new_server = pybitlaunch.Server(**kwargs)
        server, err = self.client.Servers.Create(new_server)
        if err:
            raise BitLaunchAPIError(err)
        return server

    def destroy_server(self, server_id):
        err = self.client.Servers.Destroy(server_id)
        if err:
            raise BitLaunchAPIError(err)
        return True

    def list_ssh_keys(self):
        keys = self.client.SSHKeys.List()
        return keys

    def create_ssh_key(self, name, content):
        new_key = pybitlaunch.SSHKey(name=name, content=content)
        key, err = self.client.SSHKeys.Create(new_key)
        if err:
            raise BitLaunchAPIError(err)
        return key

    def delete_ssh_key(self, key_id):
        err = self.client.SSHKeys.Delete(key_id)
        if err:
            raise BitLaunchAPIError(err)
        return True

    def list_transactions(self, page=1, pPage=25):
        txs, err = self.client.Transactions.List(page=page, pPage=pPage)
        if err:
            raise BitLaunchAPIError(err)
        return txs

    def create_transaction(self, amount_usd, crypto_symbol=None, lightning_network=None):
        new_transaction = pybitlaunch.Transaction(
            amountUSD=amount_usd,
            cryptoSymbol=crypto_symbol,
            lightningNetwork=lightning_network
        )
        transaction, err = self.client.Transactions.Create(new_transaction)
        if err:
            raise BitLaunchAPIError(err)
        return transaction

    def get_transaction(self, transaction_id):
        transaction, err = self.client.Transactions.Show(transaction_id)
        if err:
            raise BitLaunchAPIError(err)
        return transaction 