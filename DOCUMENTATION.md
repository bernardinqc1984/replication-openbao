# OpenBao Inter-Site Replication - Detailed Documentation

## Overview

This Python program implements inter-site replication for OpenBao, replicating the performance replication functionality found in Vault Enterprise. It provides active-passive replication between OpenBao instances, ensuring that all data from the primary cluster is synchronized to the secondary cluster.

## Key Features

### ✅ Complete Data Synchronization
- **Secret Engines**: All custom secret engines are replicated with their configurations
- **Authentication Methods**: All auth methods (except token auth) are replicated
- **Policies**: All custom policies are synchronized
- **Secrets**: All secrets and KV data are replicated recursively
- **Metadata**: Engine configurations, descriptions, and options are preserved

### ✅ Active-Passive Replication
- Primary cluster remains active and accepts writes
- Secondary cluster is passive and receives data
- Secondary root token is preserved during replication

### ✅ API-Based Communication
- Uses OpenBao REST API on port 8201
- Supports both HTTP and HTTPS
- Configurable SSL verification
- Timeout and retry handling

### ✅ Flexible Configuration
- YAML configuration files
- Environment variable support
- CLI parameter overrides
- Exclude path patterns

## Architecture

```
┌─────────────────┐    API Calls     ┌─────────────────┐
│   Primary       │◄────────────────►│   Secondary     │
│   OpenBao       │    Port 8201     │   OpenBao       │
│   (Active)      │                  │   (Passive)     │
└─────────────────┘                  └─────────────────┘
         ▲                                    │
         │                                    │
         │            ┌─────────────────┐     │
         └────────────│  Replication    │─────┘
                      │  Tool           │
                      │  (Python)       │
                      └─────────────────┘
```

## Installation and Setup

### Prerequisites
- Python 3.7 or higher
- Network access to both OpenBao instances
- Root tokens for both primary and secondary instances

### Quick Setup
```bash
# Clone or download the replication tool
cd Replication-Openbao

# Run the setup script
./setup.sh

# Activate the virtual environment
source venv/bin/activate
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Configuration File (config.yaml)
```yaml
primary:
  url: "https://primary-openbao.example.com:8201"
  token: "hvs.your-primary-root-token"
  
secondary:
  url: "https://secondary-openbao.example.com:8201" 
  token: "hvs.your-secondary-root-token"
  
replication:
  sync_interval: 300  # seconds
  verify_ssl: false   # set to true for production
  timeout: 30
  exclude_paths:
    - "sys/"          # system paths (automatically excluded)
    - "identity/"     # identity paths (automatically excluded)
  
logging:
  level: "INFO"       # DEBUG, INFO, WARNING, ERROR
  file: "replication.log"
```

### Environment Variables
```bash
# Primary OpenBao
export OPENBAO_PRIMARY_URL="https://primary:8201"
export OPENBAO_PRIMARY_TOKEN="hvs.your-primary-token"

# Secondary OpenBao  
export OPENBAO_SECONDARY_URL="https://secondary:8201"
export OPENBAO_SECONDARY_TOKEN="hvs.your-secondary-token"

# Optional settings
export OPENBAO_SYNC_INTERVAL=300
export OPENBAO_VERIFY_SSL=false
export OPENBAO_TIMEOUT=30
export OPENBAO_LOG_LEVEL=INFO
```

## Usage Examples

### 1. Health Check
Verify that both OpenBao instances are accessible:
```bash
python openbao_replication.py --config config.yaml --action health
```

### 2. One-Time Synchronization
Perform a complete sync from primary to secondary:
```bash
python openbao_replication.py --config config.yaml --action sync
```

### 3. Continuous Monitoring
Start continuous replication with automatic sync:
```bash
python openbao_replication.py --config config.yaml --action monitor --sync-interval 300
```

### 4. Using Environment Variables
```bash
# Set environment variables
export OPENBAO_PRIMARY_URL="https://primary:8201"
export OPENBAO_PRIMARY_TOKEN="your-token"
export OPENBAO_SECONDARY_URL="https://secondary:8201"
export OPENBAO_SECONDARY_TOKEN="your-token"

# Run without config file
python openbao_replication.py --action sync
```

### 5. Dry Run Mode
See what would be done without making changes:
```bash
python openbao_replication.py --config config.yaml --action sync --dry-run
```

## Replication Process

### Phase 1: Health Check
- Verifies connectivity to both instances
- Checks API accessibility
- Validates authentication

### Phase 2: Secondary Cleanup
- Disables all non-system secret engines
- Disables all auth methods (except token)
- Removes all custom policies
- **Preserves root token and system components**

### Phase 3: Secret Engine Replication
- Reads all secret engines from primary
- Creates matching engines on secondary
- Replicates configurations and options

### Phase 4: Auth Method Replication  
- Reads all auth methods from primary
- Creates matching methods on secondary
- Replicates configurations

### Phase 5: Policy Replication
- Reads all policies from primary
- Creates matching policies on secondary
- Preserves system policies (root, default)

### Phase 6: Secret Data Replication
- Recursively traverses all secret paths
- Reads secrets from primary
- Writes secrets to secondary
- Maintains path structure

## Security Considerations

### Authentication
- Uses root tokens for both instances
- Tokens are required for full system access
- Secondary root token is preserved during replication

### Network Security
- Supports HTTPS with certificate verification
- Configurable SSL verification (disable for self-signed certs)
- Uses standard OpenBao API port (8201)

### Data Protection
- No data is stored locally during replication
- All operations use in-memory processing
- Secure API token handling

## Monitoring and Logging

### Log Levels
- **DEBUG**: Detailed operation logs
- **INFO**: General operation status
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

### Log Output
```
2024-01-15 10:30:45 - replication.sync - INFO - Starting full synchronization
2024-01-15 10:30:46 - replication.sync - INFO - Health checks passed
2024-01-15 10:30:47 - replication.sync - INFO - Clearing secondary cluster data
2024-01-15 10:30:48 - replication.sync - INFO - Syncing secret engines
2024-01-15 10:30:49 - replication.sync - INFO - Enabling secret engine: kv/ (type: kv)
2024-01-15 10:30:50 - replication.sync - INFO - Syncing auth methods
2024-01-15 10:30:51 - replication.sync - INFO - Syncing policies
2024-01-15 10:30:52 - replication.sync - INFO - Syncing secrets
2024-01-15 10:30:55 - replication.sync - INFO - Full synchronization completed successfully
```

## Troubleshooting

### Common Issues

#### Connection Errors
```
Error: Failed to connect to OpenBao instance
```
**Solution**: Check URL, network connectivity, and firewall rules

#### Authentication Errors
```
Error: 403 Forbidden - Invalid token
```
**Solution**: Verify root token is correct and has not expired

#### SSL Certificate Errors
```
Error: SSL certificate verification failed
```
**Solution**: Set `verify_ssl: false` for self-signed certificates

#### Permission Errors
```
Error: 403 Forbidden - Insufficient permissions
```
**Solution**: Ensure tokens have root/admin privileges

### Debugging Steps

1. **Enable Debug Logging**
   ```bash
   python openbao_replication.py --config config.yaml --action health --log-level DEBUG
   ```

2. **Check Individual Components**
   ```python
   # Test connection
   python examples.py manual
   ```

3. **Verify Configuration**
   ```bash
   python openbao_replication.py --config config.yaml --action health
   ```

## Advanced Usage

### Custom Exclude Patterns
```yaml
replication:
  exclude_paths:
    - "sys/"           # System paths
    - "identity/"      # Identity system
    - "temp/"          # Temporary secrets
    - "test/"          # Test data
```

### Programmatic Usage
```python
from replication.config import ReplicationConfig
from replication.client import OpenBaoClient
from replication.sync import ReplicationSynchronizer

# Load configuration
config = ReplicationConfig('config.yaml')

# Create clients
primary = OpenBaoClient(
    url=config.get('primary', 'url'),
    token=config.get('primary', 'token')
)

secondary = OpenBaoClient(
    url=config.get('secondary', 'url'),
    token=config.get('secondary', 'token')
)

# Create synchronizer and run
sync = ReplicationSynchronizer(primary, secondary)
success = sync.full_sync()
```

## Performance Considerations

### Large Datasets
- Replication time scales with data volume
- Memory usage is minimal (streaming operations)
- Network bandwidth is the primary bottleneck

### Optimization Tips
- Use fast network connections between sites
- Schedule replication during low-usage periods
- Monitor log files for performance metrics
- Adjust timeout values for slow networks

## Production Deployment

### Recommended Setup
1. **Dedicated Service Account**: Create specific tokens for replication
2. **Monitoring**: Set up log monitoring and alerting
3. **Scheduling**: Use cron or systemd for automated execution
4. **Backup**: Maintain configuration backups
5. **Testing**: Regular disaster recovery testing

### Systemd Service Example
```ini
[Unit]
Description=OpenBao Replication Service
After=network.target

[Service]
Type=simple
User=openbao
WorkingDirectory=/opt/openbao-replication
ExecStart=/opt/openbao-replication/venv/bin/python openbao_replication.py --config production.yaml --action monitor
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### Cron Job Example
```bash
# Run replication every 5 minutes
*/5 * * * * cd /opt/openbao-replication && ./venv/bin/python openbao_replication.py --config production.yaml --action sync >> /var/log/openbao-replication.log 2>&1
```

## Limitations and Known Issues

### Current Limitations
1. **One-way replication only** (primary to secondary)
2. **No conflict resolution** (secondary changes are overwritten)
3. **No incremental sync** (performs full sync each time)
4. **Root token required** (cannot use limited permissions)

### Future Enhancements
- Incremental synchronization based on change detection
- Bidirectional replication support
- Conflict resolution strategies
- Fine-grained permission support
- Performance optimizations for large datasets

## API Reference

### Core Classes

#### ReplicationConfig
Manages configuration loading and validation.

#### OpenBaoClient  
Provides OpenBao API interaction methods.

#### ReplicationSynchronizer
Implements the core replication logic.

### CLI Interface
All CLI options and their usage patterns.

This documentation provides comprehensive guidance for implementing OpenBao inter-site replication in your environment. The tool is designed to be robust, configurable, and suitable for production use while maintaining the security and reliability expected in enterprise environments.
