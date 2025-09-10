"""
Synchronization logic for OpenBao replication
"""
import logging
import time
from typing import Dict, Any, List, Set
from .client import OpenBaoClient

logger = logging.getLogger(__name__)

class ReplicationSynchronizer:
    """Handles synchronization between primary and secondary OpenBao instances"""
    
    def __init__(self, primary_client: OpenBaoClient, secondary_client: OpenBaoClient, 
                 exclude_paths: List[str] = None):
        """Initialize synchronizer"""
        self.primary = primary_client
        self.secondary = secondary_client
        self.exclude_paths = exclude_paths or []
        
    def should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from replication"""
        for exclude in self.exclude_paths:
            if path.startswith(exclude):
                return True
        return False
    
    def full_sync(self) -> bool:
        """Perform full synchronization from primary to secondary"""
        logger.info("Starting full synchronization")
        
        # Health checks
        if not self._health_check():
            return False
        
        # Clear secondary (except root token)
        if not self._clear_secondary():
            return False
        
        # Sync in order: secret engines, auth methods, policies, secrets
        success = True
        success &= self._sync_secret_engines()
        success &= self._sync_auth_methods()
        success &= self._sync_policies()
        success &= self._sync_secrets()
        
        if success:
            logger.info("Full synchronization completed successfully")
        else:
            logger.error("Full synchronization completed with errors")
        
        return success
    
    def _health_check(self) -> bool:
        """Check health of both instances"""
        logger.info("Performing health checks")
        
        if not self.primary.health_check():
            logger.error("Primary OpenBao instance is not healthy")
            return False
        
        if not self.secondary.health_check():
            logger.error("Secondary OpenBao instance is not healthy")
            return False
        
        logger.info("Health checks passed")
        return True
    
    def _clear_secondary(self) -> bool:
        """Clear secondary cluster data while preserving root token"""
        logger.info("Clearing secondary cluster data")
        
        try:
            # Disable all non-system secret engines
            secret_engines = self.secondary.list_secret_engines()
            for path, config in secret_engines.items():
                if not path.startswith('sys/') and not path.startswith('identity/'):
                    logger.info(f"Disabling secret engine: {path}")
                    self.secondary.disable_secret_engine(path.rstrip('/'))
            
            # Disable all non-system auth methods (except token)
            auth_methods = self.secondary.list_auth_methods()
            for path, config in auth_methods.items():
                if path != 'token/' and not path.startswith('sys/'):
                    logger.info(f"Disabling auth method: {path}")
                    self.secondary.disable_auth_method(path.rstrip('/'))
            
            # Delete all non-system policies (except root and default)
            policies = self.secondary.list_policies()
            system_policies = {'root', 'default'}
            for policy in policies:
                if policy not in system_policies:
                    logger.info(f"Deleting policy: {policy}")
                    self.secondary.delete_policy(policy)
            
            logger.info("Secondary cluster cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear secondary cluster: {e}")
            return False
    
    def _sync_secret_engines(self) -> bool:
        """Sync secret engines from primary to secondary"""
        logger.info("Syncing secret engines")
        
        try:
            primary_engines = self.primary.list_secret_engines()
            success = True
            
            for path, config in primary_engines.items():
                if self.should_exclude_path(path):
                    logger.debug(f"Skipping excluded secret engine: {path}")
                    continue
                
                # Skip system engines
                if path.startswith('sys/') or path.startswith('identity/'):
                    continue
                
                engine_type = config.get('type')
                if not engine_type:
                    logger.warning(f"No type found for secret engine: {path}")
                    continue
                
                logger.info(f"Enabling secret engine: {path} (type: {engine_type})")
                engine_config = {
                    'description': config.get('description', ''),
                    'config': config.get('config', {}),
                    'options': config.get('options', {})
                }
                
                if not self.secondary.enable_secret_engine(path.rstrip('/'), engine_type, engine_config):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync secret engines: {e}")
            return False
    
    def _sync_auth_methods(self) -> bool:
        """Sync auth methods from primary to secondary"""
        logger.info("Syncing auth methods")
        
        try:
            primary_auth = self.primary.list_auth_methods()
            success = True
            
            for path, config in primary_auth.items():
                if self.should_exclude_path(path):
                    logger.debug(f"Skipping excluded auth method: {path}")
                    continue
                
                # Skip token auth (already exists)
                if path == 'token/':
                    continue
                
                auth_type = config.get('type')
                if not auth_type:
                    logger.warning(f"No type found for auth method: {path}")
                    continue
                
                logger.info(f"Enabling auth method: {path} (type: {auth_type})")
                auth_config = {
                    'description': config.get('description', ''),
                    'config': config.get('config', {})
                }
                
                if not self.secondary.enable_auth_method(path.rstrip('/'), auth_type, auth_config):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync auth methods: {e}")
            return False
    
    def _sync_policies(self) -> bool:
        """Sync policies from primary to secondary"""
        logger.info("Syncing policies")
        
        try:
            primary_policies = self.primary.list_policies()
            system_policies = {'root', 'default'}
            success = True
            
            for policy_name in primary_policies:
                if policy_name in system_policies:
                    continue
                
                policy_content = self.primary.read_policy(policy_name)
                if policy_content is None:
                    logger.warning(f"Could not read policy: {policy_name}")
                    continue
                
                logger.info(f"Syncing policy: {policy_name}")
                if not self.secondary.write_policy(policy_name, policy_content):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync policies: {e}")
            return False
    
    def _sync_secrets(self) -> bool:
        """Sync all secrets from primary to secondary"""
        logger.info("Syncing secrets")
        
        try:
            # Get all secret engines
            secret_engines = self.primary.list_secret_engines()
            success = True
            
            for mount_path, config in secret_engines.items():
                if self.should_exclude_path(mount_path):
                    continue
                
                # Skip system mounts
                if mount_path.startswith('sys/') or mount_path.startswith('identity/'):
                    continue
                
                logger.info(f"Syncing secrets from mount: {mount_path}")
                if not self._sync_secrets_recursive(mount_path.rstrip('/'), ''):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync secrets: {e}")
            return False
    
    def _sync_secrets_recursive(self, mount_path: str, sub_path: str) -> bool:
        """Recursively sync secrets in a path"""
        full_path = f"{mount_path}/{sub_path}".rstrip('/')
        
        try:
            # List secrets at current path
            keys = self.primary.list_secrets(full_path)
            success = True
            
            for key in keys:
                current_path = f"{full_path}/{key}".strip('/')
                
                if key.endswith('/'):
                    # It's a directory, recurse
                    if not self._sync_secrets_recursive(mount_path, f"{sub_path}/{key}".strip('/')):
                        success = False
                else:
                    # It's a secret, sync it
                    logger.debug(f"Syncing secret: {current_path}")
                    secret_data = self.primary.read_secret(current_path)
                    
                    if secret_data:
                        if not self.secondary.write_secret(current_path, secret_data):
                            success = False
                            logger.error(f"Failed to write secret: {current_path}")
                    else:
                        logger.warning(f"Could not read secret: {current_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync secrets in path {full_path}: {e}")
            return False
    
    def incremental_sync(self) -> bool:
        """Perform incremental synchronization (simplified for this implementation)"""
        logger.info("Performing incremental synchronization")
        # For simplicity, this does a full sync
        # In a production implementation, this would track changes
        return self.full_sync()
    
    def monitor_and_sync(self, interval: int = 300):
        """Continuously monitor and sync changes"""
        logger.info(f"Starting continuous monitoring with {interval}s interval")
        
        while True:
            try:
                self.incremental_sync()
                logger.info(f"Sleeping for {interval} seconds")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                time.sleep(30)  # Wait before retrying
