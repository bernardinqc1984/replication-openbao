#!/usr/bin/env python3
"""
OpenBao Inter-Site Replication Tool

This tool enables inter-site replication for OpenBao, mimicking Vault Enterprise
performance replication functionality.
"""

import click
import logging
import sys
import os
from pathlib import Path

# Add the current directory to the path to import replication modules
sys.path.insert(0, str(Path(__file__).parent))

from replication.config import ReplicationConfig
from replication.client import OpenBaoClient
from replication.sync import ReplicationSynchronizer

def setup_logging(level: str, log_file: str = None):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

@click.command()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Configuration file path')
@click.option('--action', '-a', 
              type=click.Choice(['sync', 'monitor', 'health']), 
              default='sync',
              help='Action to perform')
@click.option('--primary-url', 
              envvar='OPENBAO_PRIMARY_URL',
              help='Primary OpenBao URL')
@click.option('--primary-token', 
              envvar='OPENBAO_PRIMARY_TOKEN',
              help='Primary OpenBao token')
@click.option('--secondary-url', 
              envvar='OPENBAO_SECONDARY_URL',
              help='Secondary OpenBao URL')
@click.option('--secondary-token', 
              envvar='OPENBAO_SECONDARY_TOKEN',
              help='Secondary OpenBao token')
@click.option('--verify-ssl/--no-verify-ssl', 
              default=False,
              help='Verify SSL certificates')
@click.option('--sync-interval', 
              type=int, 
              default=300,
              help='Sync interval in seconds for monitor mode')
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default='INFO',
              help='Logging level')
@click.option('--log-file', 
              help='Log file path')
@click.option('--dry-run', 
              is_flag=True,
              help='Dry run mode (show what would be done)')
def main(config, action, primary_url, primary_token, secondary_url, 
         secondary_token, verify_ssl, sync_interval, log_level, log_file, dry_run):
    """
    OpenBao Inter-Site Replication Tool
    
    Enables active-passive replication between OpenBao instances.
    
    Examples:
    
    \b
    # One-time sync using config file
    python openbao_replication.py --config config.yaml --action sync
    
    \b
    # Continuous monitoring using environment variables
    export OPENBAO_PRIMARY_URL="https://primary:8201"
    export OPENBAO_PRIMARY_TOKEN="root-token"
    export OPENBAO_SECONDARY_URL="https://secondary:8201" 
    export OPENBAO_SECONDARY_TOKEN="root-token"
    python openbao_replication.py --action monitor
    
    \b
    # Health check
    python openbao_replication.py --action health
    """
    
    try:
        # Load configuration
        if config:
            replication_config = ReplicationConfig(config)
        else:
            replication_config = ReplicationConfig()
        
        # Override with CLI parameters
        if primary_url:
            replication_config.config['primary']['url'] = primary_url
        if primary_token:
            replication_config.config['primary']['token'] = primary_token
        if secondary_url:
            replication_config.config['secondary']['url'] = secondary_url
        if secondary_token:
            replication_config.config['secondary']['token'] = secondary_token
        if verify_ssl is not None:
            replication_config.config['replication']['verify_ssl'] = verify_ssl
        if sync_interval:
            replication_config.config['replication']['sync_interval'] = sync_interval
        if log_level:
            replication_config.config['logging']['level'] = log_level
        if log_file:
            replication_config.config['logging']['file'] = log_file
        
        # Validate configuration
        replication_config.validate()
        
        # Setup logging
        setup_logging(
            replication_config.get('logging', 'level'),
            replication_config.get('logging', 'file')
        )
        
        logger = logging.getLogger(__name__)
        logger.info("OpenBao Replication Tool starting")
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        # Create clients
        primary_client = OpenBaoClient(
            url=replication_config.get('primary', 'url'),
            token=replication_config.get('primary', 'token'),
            verify_ssl=replication_config.get('replication', 'verify_ssl'),
            timeout=replication_config.get('replication', 'timeout')
        )
        
        secondary_client = OpenBaoClient(
            url=replication_config.get('secondary', 'url'),
            token=replication_config.get('secondary', 'token'),
            verify_ssl=replication_config.get('replication', 'verify_ssl'),
            timeout=replication_config.get('replication', 'timeout')
        )
        
        # Create synchronizer
        synchronizer = ReplicationSynchronizer(
            primary_client=primary_client,
            secondary_client=secondary_client,
            exclude_paths=replication_config.get('replication', 'exclude_paths')
        )
        
        # Execute action
        if action == 'health':
            logger.info("Performing health checks")
            primary_healthy = primary_client.health_check()
            secondary_healthy = secondary_client.health_check()
            
            click.echo(f"Primary ({replication_config.get('primary', 'url')}): {'✓ Healthy' if primary_healthy else '✗ Unhealthy'}")
            click.echo(f"Secondary ({replication_config.get('secondary', 'url')}): {'✓ Healthy' if secondary_healthy else '✗ Unhealthy'}")
            
            if not (primary_healthy and secondary_healthy):
                sys.exit(1)
        
        elif action == 'sync':
            if dry_run:
                logger.info("Would perform full synchronization")
                logger.info("Configuration:")
                logger.info(f"  Primary: {replication_config.get('primary', 'url')}")
                logger.info(f"  Secondary: {replication_config.get('secondary', 'url')}")
                logger.info(f"  Exclude paths: {replication_config.get('replication', 'exclude_paths')}")
            else:
                logger.info("Performing full synchronization")
                success = synchronizer.full_sync()
                if not success:
                    logger.error("Synchronization failed")
                    sys.exit(1)
                logger.info("Synchronization completed successfully")
        
        elif action == 'monitor':
            if dry_run:
                logger.info(f"Would start monitoring with {sync_interval}s interval")
            else:
                logger.info("Starting monitoring mode")
                synchronizer.monitor_and_sync(sync_interval)
        
        logger.info("OpenBao Replication Tool completed")
        
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logging.getLogger(__name__).exception("Unhandled exception")
        sys.exit(1)

if __name__ == '__main__':
    main()
