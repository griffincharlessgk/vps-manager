import requests
import json
from typing import Dict, List, Optional, Any

class CloudFlyAPIError(Exception):
    """Custom exception for CloudFly API errors"""
    pass

class CloudFlyClient:
    """Client for interacting with CloudFly API"""
    
    def __init__(self, token: str, base_url: str = "https://api.cloudfly.vn"):
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to CloudFly API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise CloudFlyAPIError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise CloudFlyAPIError(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise CloudFlyAPIError(f"Invalid JSON response: {str(e)}")
    
    def get_user_info(self) -> Dict:
        """Get current user information"""
        return self._make_request('GET', '/backend/api/users')
    
    def list_instances(self) -> List[Dict]:
        """List all VPS instances"""
        response = self._make_request('GET', '/backend/api/instances')
        # CloudFly API trả về object với 'results' chứa danh sách instances
        if isinstance(response, dict) and 'results' in response:
            return response['results']
        # Fallback cho trường hợp API trả về trực tiếp danh sách
        if isinstance(response, list):
            return response
        # Hoặc có thể có wrapper object khác
        return response.get('instances', [])
    
    def get_instance(self, instance_id: str) -> Dict:
        """Get specific instance details"""
        return self._make_request('GET', f'/backend/api/instances/{instance_id}')
    
    def create_instance(self, **kwargs) -> Dict:
        """Create a new VPS instance"""
        payload = {
            "region": kwargs.get("region", "HN-Cloud01"),
            "image_name": kwargs.get("image_name", "CentOS-7.9"),
            "flavor_type": kwargs.get("flavor_type", "Standard"),
            "ram": kwargs.get("ram", 1),
            "vcpus": kwargs.get("vcpus", 1),
            "disk": kwargs.get("disk", 20),
            "enable_ipv6": kwargs.get("enable_ipv6", False),
            "enable_private_network": kwargs.get("enable_private_network", False),
            "auto_backup": kwargs.get("auto_backup", False)
        }
        
        # Add optional parameters if provided
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "ssh_key_id" in kwargs:
            payload["ssh_key_id"] = kwargs["ssh_key_id"]
        
        return self._make_request('POST', '/backend/api/instances', payload)
    
    def delete_instance(self, instance_id: str) -> bool:
        """Delete a VPS instance"""
        self._make_request('DELETE', f'/backend/api/instances/{instance_id}')
        return True
    
    def start_instance(self, instance_id: str) -> Dict:
        """Start a VPS instance"""
        return self._make_request('POST', f'/backend/api/instances/{instance_id}/start')
    
    def stop_instance(self, instance_id: str) -> Dict:
        """Stop a VPS instance"""
        return self._make_request('POST', f'/backend/api/instances/{instance_id}/stop')
    
    def restart_instance(self, instance_id: str) -> Dict:
        """Restart a VPS instance"""
        return self._make_request('POST', f'/backend/api/instances/{instance_id}/restart')
    
    def list_regions(self) -> List[Dict]:
        """List available regions"""
        response = self._make_request('GET', '/backend/api/regions')
        return response.get('regions', [])
    
    def list_images(self) -> List[Dict]:
        """List available images"""
        response = self._make_request('GET', '/backend/api/images')
        return response.get('images', [])
    
    def list_flavors(self) -> List[Dict]:
        """List available flavors/plans"""
        response = self._make_request('GET', '/backend/api/flavors')
        return response.get('flavors', [])
    
    def list_ssh_keys(self) -> List[Dict]:
        """List SSH keys"""
        response = self._make_request('GET', '/backend/api/ssh-keys')
        return response.get('ssh_keys', [])
    
    def create_ssh_key(self, name: str, public_key: str) -> Dict:
        """Create a new SSH key"""
        payload = {
            "name": name,
            "public_key": public_key
        }
        return self._make_request('POST', '/backend/api/ssh-keys', payload)
    
    def delete_ssh_key(self, key_id: str) -> bool:
        """Delete an SSH key"""
        self._make_request('DELETE', f'/backend/api/ssh-keys/{key_id}')
        return True
    
    def get_billing_info(self) -> Dict:
        """Get billing information"""
        return self._make_request('GET', '/backend/api/billing')
    
    def get_usage_stats(self, period: str = "current") -> Dict:
        """Get usage statistics"""
        return self._make_request('GET', f'/backend/api/usage?period={period}') 