"""
OpenBao API client for replication operations
"""
import requests
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class OpenBaoClient:
    """Client for interacting with OpenBao API"""
    
    def __init__(self, url: str, token: str, verify_ssl: bool = False, timeout: int = 30):
        """Initialize OpenBao client"""
        self.url = url.rstrip('/')
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'X-Vault-Token': token,
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make authenticated request to OpenBao"""
        url = urljoin(self.url + '/', path.lstrip('/'))
        kwargs.setdefault('verify', self.verify_ssl)
        kwargs.setdefault('timeout', self.timeout)
        
        logger.debug(f"{method} {url}")
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code >= 400:
            logger.error(f"Request failed: {method} {url} - {response.status_code} - {response.text}")
            response.raise_for_status()
        
        return response
    
    def get(self, path: str, **kwargs) -> requests.Response:
        """GET request"""
        return self._make_request('GET', path, **kwargs)
    
    def post(self, path: str, data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """POST request"""
        if data:
            kwargs['json'] = data
        return self._make_request('POST', path, **kwargs)
    
    def put(self, path: str, data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """PUT request"""
        if data:
            kwargs['json'] = data
        return self._make_request('PUT', path, **kwargs)
    
    def delete(self, path: str, **kwargs) -> requests.Response:
        """DELETE request"""
        return self._make_request('DELETE', path, **kwargs)
    
    def list_secrets(self, path: str = '') -> List[str]:
        """List secrets at a given path"""
        try:
            response = self.get(f'v1/{path}', params={'list': 'true'})
            data = response.json()
            return data.get('data', {}).get('keys', [])
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to list secrets at {path}: {e}")
            return []
    
    def read_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """Read secret at path"""
        try:
            response = self.get(f'v1/{path}')
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to read secret at {path}: {e}")
            return None
    
    def write_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Write secret to path"""
        try:
            self.post(f'v1/{path}', data=data)
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to write secret to {path}: {e}")
            return False
    
    def delete_secret(self, path: str) -> bool:
        """Delete secret at path"""
        try:
            self.delete(f'v1/{path}')
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to delete secret at {path}: {e}")
            return False
    
    def list_auth_methods(self) -> Dict[str, Any]:
        """List authentication methods"""
        try:
            response = self.get('v1/sys/auth')
            return response.json().get('data', {})
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list auth methods: {e}")
            return {}
    
    def enable_auth_method(self, path: str, auth_type: str, config: Dict[str, Any] = None) -> bool:
        """Enable authentication method"""
        try:
            data = {'type': auth_type}
            if config:
                data.update(config)
            self.post(f'v1/sys/auth/{path}', data=data)
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to enable auth method {path}: {e}")
            return False
    
    def disable_auth_method(self, path: str) -> bool:
        """Disable authentication method"""
        try:
            self.delete(f'v1/sys/auth/{path}')
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to disable auth method {path}: {e}")
            return False
    
    def list_secret_engines(self) -> Dict[str, Any]:
        """List secret engines"""
        try:
            response = self.get('v1/sys/mounts')
            return response.json().get('data', {})
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list secret engines: {e}")
            return {}
    
    def enable_secret_engine(self, path: str, engine_type: str, config: Dict[str, Any] = None) -> bool:
        """Enable secret engine"""
        try:
            data = {'type': engine_type}
            if config:
                data.update(config)
            self.post(f'v1/sys/mounts/{path}', data=data)
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to enable secret engine {path}: {e}")
            return False
    
    def disable_secret_engine(self, path: str) -> bool:
        """Disable secret engine"""
        try:
            self.delete(f'v1/sys/mounts/{path}')
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to disable secret engine {path}: {e}")
            return False
    
    def list_policies(self) -> List[str]:
        """List policies"""
        try:
            response = self.get('v1/sys/policies/acl')
            data = response.json()
            return data.get('data', {}).get('keys', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list policies: {e}")
            return []
    
    def read_policy(self, name: str) -> Optional[str]:
        """Read policy"""
        try:
            response = self.get(f'v1/sys/policies/acl/{name}')
            data = response.json()
            return data.get('data', {}).get('policy', '')
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to read policy {name}: {e}")
            return None
    
    def write_policy(self, name: str, policy: str) -> bool:
        """Write policy"""
        try:
            self.put(f'v1/sys/policies/acl/{name}', data={'policy': policy})
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to write policy {name}: {e}")
            return False
    
    def delete_policy(self, name: str) -> bool:
        """Delete policy"""
        try:
            self.delete(f'v1/sys/policies/acl/{name}')
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to delete policy {name}: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if OpenBao is healthy and accessible"""
        try:
            response = self.get('v1/sys/health')
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
