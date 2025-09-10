"""
Configuration management for OpenBao replication
"""
import os
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class ReplicationConfig:
    """Manages configuration for OpenBao replication"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from file and environment variables"""
        load_dotenv()
        
        self.config = self._load_default_config()
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                self._merge_config(self.config, file_config)
        
        # Override with environment variables
        self._load_env_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'primary': {
                'url': 'https://localhost:8201',
                'token': '',
            },
            'secondary': {
                'url': 'https://localhost:8202',
                'token': '',
            },
            'replication': {
                'sync_interval': 300,
                'verify_ssl': False,
                'timeout': 30,
                'exclude_paths': ['sys/', 'identity/'],
            },
            'logging': {
                'level': 'INFO',
                'file': 'replication.log',
            }
        }
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_env_config(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'OPENBAO_PRIMARY_URL': ('primary', 'url'),
            'OPENBAO_PRIMARY_TOKEN': ('primary', 'token'),
            'OPENBAO_SECONDARY_URL': ('secondary', 'url'),
            'OPENBAO_SECONDARY_TOKEN': ('secondary', 'token'),
            'OPENBAO_SYNC_INTERVAL': ('replication', 'sync_interval'),
            'OPENBAO_VERIFY_SSL': ('replication', 'verify_ssl'),
            'OPENBAO_TIMEOUT': ('replication', 'timeout'),
            'OPENBAO_LOG_LEVEL': ('logging', 'level'),
            'OPENBAO_LOG_FILE': ('logging', 'file'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if env_var in ['OPENBAO_SYNC_INTERVAL', 'OPENBAO_TIMEOUT']:
                    value = int(value)
                elif env_var == 'OPENBAO_VERIFY_SSL':
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                self.config[section][key] = value
    
    def get(self, *keys):
        """Get nested configuration value"""
        value = self.config
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value
    
    def validate(self) -> bool:
        """Validate required configuration"""
        required_fields = [
            ('primary', 'url'),
            ('primary', 'token'),
            ('secondary', 'url'),
            ('secondary', 'token'),
        ]
        
        for section, key in required_fields:
            if not self.get(section, key):
                raise ValueError(f"Missing required configuration: {section}.{key}")
        
        return True
