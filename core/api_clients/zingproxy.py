import requests
from typing import Optional, Dict, Any, List

class ZingProxyAPIError(Exception):
    pass

class ZingProxyClient:
    BASE_URL = 'https://api.zingproxy.com'

    def __init__(self, email: str = None, password: str = None, access_token: Optional[str] = None):
        self.email = email
        self.password = password
        self.access_token = access_token
        if not self.access_token and email and password:
            self.login()

    def login(self):
        url = f'{self.BASE_URL}/account/access-token'
        resp = requests.post(url, json={"email": self.email, "password": self.password}, timeout=10)
        if resp.status_code != 200:
            raise ZingProxyAPIError(f"Login failed: {resp.status_code} {resp.text}")
        data = resp.json()
        if data.get('status') != 'success' or 'accessToken' not in data:
            raise ZingProxyAPIError(f"Login failed: {data}")
        self.access_token = data['accessToken']

    def get_account_details(self) -> Dict[str, Any]:
        url = f'{self.BASE_URL}/account/details'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            raise ZingProxyAPIError(f"Get account details failed: {resp.status_code} {resp.text}")
        data = resp.json()
        # Chuẩn hóa trả về user (bao gồm balance)
        if data.get('status') == 'success' and 'user' in data:
            return data['user']
        return {}

    def get_all_active_proxies(self) -> List[Dict[str, Any]]:
        url = f'{self.BASE_URL}/proxy/get-all-active-proxies'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            raise ZingProxyAPIError(f"Get proxies failed: {resp.status_code} {resp.text}")
        
        data = resp.json()
        # Xử lý format mới từ API
        proxies = []
        
        # Thêm datacenter IPv4 proxies
        if 'datacenterIPv4Proxies' in data:
            for proxy in data['datacenterIPv4Proxies']:
                proxies.append(self._normalize_proxy_data(proxy, 'datacenter_ipv4'))
        
        # Thêm datacenter IPv6 proxies  
        if 'datacenterIPv6Proxies' in data:
            for proxy in data['datacenterIPv6Proxies']:
                proxies.append(self._normalize_proxy_data(proxy, 'datacenter_ipv6'))
        
        # Thêm Vietnam residential proxies
        if 'vietnamResidentialProxies' in data:
            for proxy in data['vietnamResidentialProxies']:
                proxies.append(self._normalize_proxy_data(proxy, 'vietnam_residential'))
        
        return proxies

    def _normalize_proxy_data(self, proxy: Dict[str, Any], proxy_type: str) -> Dict[str, Any]:
        """Chuẩn hóa dữ liệu proxy từ API về format thống nhất"""
        return {
            'proxy_id': proxy.get('uId') or proxy.get('resourceId'),
            'ip': proxy.get('ip') or proxy.get('hostIp'),
            'port': proxy.get('portHttp'),  # Sử dụng port HTTP làm port chính
            'port_socks5': proxy.get('portSocks5'),
            'status': proxy.get('state'),
            'expire_at': proxy.get('dateEnd'),
            'location': proxy.get('countryCode', 'vn'),
            'type': proxy_type,
            'username': proxy.get('username'),
            'password': proxy.get('password'),
            'note': proxy.get('note'),
            'created_at': proxy.get('createdAt'),
            'auto_renew': proxy.get('autoRenew'),
            'prices': proxy.get('prices'),
            'link_change_ip': proxy.get('linkChangeIp')
        }

    def get_proxies_by_status(self, status: str) -> List[Dict[str, Any]]:
        # status: running, expiring, cancelled, all
        url = f'{self.BASE_URL}/proxy/dan-cu-viet-nam/{status}'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            raise ZingProxyAPIError(f"Get proxies by status failed: {resp.status_code} {resp.text}")
        return resp.json().get('data', []) 