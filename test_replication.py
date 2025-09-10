"""
Test suite for OpenBao replication functionality
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import replication modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from replication.config import ReplicationConfig
from replication.client import OpenBaoClient
from replication.sync import ReplicationSynchronizer

class TestReplicationConfig(unittest.TestCase):
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration loading"""
        config = ReplicationConfig()
        self.assertIsNotNone(config.get('primary', 'url'))
        self.assertIsNotNone(config.get('secondary', 'url'))
    
    def test_env_override(self):
        """Test environment variable override"""
        with patch.dict(os.environ, {
            'OPENBAO_PRIMARY_URL': 'https://test-primary:8201',
            'OPENBAO_PRIMARY_TOKEN': 'test-token'
        }):
            config = ReplicationConfig()
            self.assertEqual(config.get('primary', 'url'), 'https://test-primary:8201')
            self.assertEqual(config.get('primary', 'token'), 'test-token')

class TestOpenBaoClient(unittest.TestCase):
    """Test OpenBao API client"""
    
    def setUp(self):
        """Set up test client"""
        self.client = OpenBaoClient(
            url='https://test:8201',
            token='test-token',
            verify_ssl=False
        )
    
    @patch('requests.Session.request')
    def test_health_check(self, mock_request):
        """Test health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        result = self.client.health_check()
        self.assertTrue(result)
    
    @patch('requests.Session.request')
    def test_list_secrets(self, mock_request):
        """Test listing secrets"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'keys': ['secret1', 'secret2/']}
        }
        mock_request.return_value = mock_response
        
        result = self.client.list_secrets('secret/')
        self.assertEqual(result, ['secret1', 'secret2/'])

class TestReplicationSynchronizer(unittest.TestCase):
    """Test replication synchronizer"""
    
    def setUp(self):
        """Set up test synchronizer"""
        self.primary_client = Mock(spec=OpenBaoClient)
        self.secondary_client = Mock(spec=OpenBaoClient)
        self.sync = ReplicationSynchronizer(
            self.primary_client,
            self.secondary_client,
            exclude_paths=['sys/', 'identity/']
        )
    
    def test_should_exclude_path(self):
        """Test path exclusion"""
        self.assertTrue(self.sync.should_exclude_path('sys/auth'))
        self.assertTrue(self.sync.should_exclude_path('identity/entity'))
        self.assertFalse(self.sync.should_exclude_path('secret/myapp'))
    
    def test_health_check(self):
        """Test health check"""
        self.primary_client.health_check.return_value = True
        self.secondary_client.health_check.return_value = True
        
        result = self.sync._health_check()
        self.assertTrue(result)
        
        self.primary_client.health_check.assert_called_once()
        self.secondary_client.health_check.assert_called_once()

if __name__ == '__main__':
    unittest.main()
