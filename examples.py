#!/usr/bin/env python3
"""
Example usage of the OpenBao Replication Tool
"""

import time
import logging
from replication.config import ReplicationConfig
from replication.client import OpenBaoClient
from replication.sync import ReplicationSynchronizer

def example_basic_usage():
    """Example of basic replication usage"""
    print("=== Basic OpenBao Replication Example ===")
    
    # Load configuration
    config = ReplicationConfig('config.yaml')
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create clients
    primary = OpenBaoClient(
        url=config.get('primary', 'url'),
        token=config.get('primary', 'token'),
        verify_ssl=config.get('replication', 'verify_ssl')
    )
    
    secondary = OpenBaoClient(
        url=config.get('secondary', 'url'),
        token=config.get('secondary', 'token'),
        verify_ssl=config.get('replication', 'verify_ssl')
    )
    
    # Create synchronizer
    sync = ReplicationSynchronizer(
        primary_client=primary,
        secondary_client=secondary,
        exclude_paths=config.get('replication', 'exclude_paths')
    )
    
    # Perform health check
    print("Checking health...")
    if not primary.health_check():
        print("Primary OpenBao is not healthy")
        return
    
    if not secondary.health_check():
        print("Secondary OpenBao is not healthy")
        return
    
    print("Both instances are healthy")
    
    # Perform one-time sync
    print("Starting replication...")
    success = sync.full_sync()
    
    if success:
        print("Replication completed successfully")
    else:
        print("Replication failed")

def example_continuous_monitoring():
    """Example of continuous monitoring"""
    print("=== Continuous Monitoring Example ===")
    
    config = ReplicationConfig('config.yaml')
    
    primary = OpenBaoClient(
        url=config.get('primary', 'url'),
        token=config.get('primary', 'token'),
        verify_ssl=config.get('replication', 'verify_ssl')
    )
    
    secondary = OpenBaoClient(
        url=config.get('secondary', 'url'),
        token=config.get('secondary', 'token'),
        verify_ssl=config.get('replication', 'verify_ssl')
    )
    
    sync = ReplicationSynchronizer(primary, secondary)
    
    # Start monitoring (this will run indefinitely)
    print("Starting continuous monitoring...")
    print("Press Ctrl+C to stop")
    
    try:
        sync.monitor_and_sync(interval=config.get('replication', 'sync_interval'))
    except KeyboardInterrupt:
        print("Monitoring stopped")

def example_manual_operations():
    """Example of manual operations"""
    print("=== Manual Operations Example ===")
    
    config = ReplicationConfig('config.yaml')
    
    primary = OpenBaoClient(
        url=config.get('primary', 'url'),
        token=config.get('primary', 'token'),
        verify_ssl=config.get('replication', 'verify_ssl')
    )
    
    # List secret engines on primary
    print("Secret engines on primary:")
    engines = primary.list_secret_engines()
    for path, engine_config in engines.items():
        print(f"  {path} ({engine_config.get('type', 'unknown')})")
    
    # List auth methods on primary
    print("\nAuth methods on primary:")
    auth_methods = primary.list_auth_methods()
    for path, auth_config in auth_methods.items():
        print(f"  {path} ({auth_config.get('type', 'unknown')})")
    
    # List policies on primary
    print("\nPolicies on primary:")
    policies = primary.list_policies()
    for policy in policies:
        print(f"  {policy}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python examples.py [basic|monitor|manual]")
        sys.exit(1)
    
    example_type = sys.argv[1]
    
    if example_type == 'basic':
        example_basic_usage()
    elif example_type == 'monitor':
        example_continuous_monitoring()
    elif example_type == 'manual':
        example_manual_operations()
    else:
        print("Unknown example type. Use: basic, monitor, or manual")
        sys.exit(1)
