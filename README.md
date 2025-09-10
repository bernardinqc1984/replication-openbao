# OpenBao Inter-Site Replication

This Python program enables inter-site replication for OpenBao, replicating the performance replication functionality found in Vault Enterprise.

## Features

- Active-passive replication mode
- Complete data synchronization (secrets, KV paths, auth paths, metadata)
- Secondary cluster data erasure before sync
- API-based communication on port 8201
- CLI interface with configuration file support
- Root token preservation on secondary

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.yaml` file:

```yaml
primary:
  url: "https://primary-openbao:8201"
  token: "your-primary-root-token"
  
secondary:
  url: "https://secondary-openbao:8201" 
  token: "your-secondary-root-token"
  
replication:
  sync_interval: 300  # seconds
  verify_ssl: false
  timeout: 30
  
logging:
  level: "INFO"
  file: "replication.log"
```

## Usage

### One-time replication
```bash
python openbao_replication.py --config config.yaml --action sync
```

### Continuous replication
```bash
python openbao_replication.py --config config.yaml --action monitor
```

### CLI Environment Variables
```bash
export OPENBAO_PRIMARY_URL="https://primary:8201"
export OPENBAO_PRIMARY_TOKEN="your-token"
export OPENBAO_SECONDARY_URL="https://secondary:8201"
export OPENBAO_SECONDARY_TOKEN="your-token"
```

## Architecture

- `openbao_replication.py` - Main CLI entry point
- `replication/` - Core replication modules
  - `client.py` - OpenBao API client
  - `sync.py` - Synchronization logic
  - `config.py` - Configuration management
