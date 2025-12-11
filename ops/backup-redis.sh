#!/bin/bash
set -e

BACKUP_DIR="/var/backups/agentsflowai"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/agentsflowai/redis-backup.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Load environment variables
if [ -f "/opt/agentsflowai/backend/.env" ]; then
    source "/opt/agentsflowai/backend/.env"
else
    echo "Error: .env file not found"
    exit 1
fi

# Check required variables
if [ -z "$REDIS_URL" ]; then
    echo "Error: REDIS_URL not set in .env"
    exit 1
fi

if [ -z "$BACKUP_ENCRYPTION_KEY" ]; then
    echo "Error: BACKUP_ENCRYPTION_KEY not set in .env"
    exit 1
fi

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Redis backup..."

# Test Redis connectivity
if ! redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1; then
    log "Error: Cannot connect to Redis at $REDIS_URL"
    exit 1
fi

# RDB Backup with compression and encryption
RDB_FILE="$BACKUP_DIR/redis_$DATE.rdb.gz.gpg"
log "Creating Redis RDB backup: $RDB_FILE"

if redis-cli -u "$REDIS_URL" --rdb - | gzip | gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --symmetric --cipher-algo AES256 -o "$RDB_FILE"; then
    log "Redis RDB backup completed successfully: $RDB_FILE"
else
    log "Error: Redis RDB backup failed"
    exit 1
fi

# Optional: Backup AOF file if it exists and is enabled
AOF_FILE="/var/lib/redis/appendonly.aof"
if [ -f "$AOF_FILE" ]; then
    AOF_BACKUP="$BACKUP_DIR/redis_aof_$DATE.aof.gz.gpg"
    log "Creating Redis AOF backup: $AOF_BACKUP"

    if gzip -c "$AOF_FILE" | gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --symmetric --cipher-algo AES256 -o "$AOF_BACKUP"; then
        log "Redis AOF backup completed successfully: $AOF_BACKUP"
    else
        log "Warning: Redis AOF backup failed, but continuing..."
    fi
fi

# Cleanup old Redis backups (30 days retention)
log "Cleaning up Redis backups older than 30 days..."
find "$BACKUP_DIR" -name "redis_*.rdb.gz.gpg" -mtime +30 -delete
find "$BACKUP_DIR" -name "redis_aof_*.aof.gz.gpg" -mtime +30 -delete

# Verify backup integrity (quick check)
if gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --decrypt "$RDB_FILE" | gunzip | head -c 9 | grep -q "REDIS"; then
    log "Backup integrity check passed"
else
    log "Warning: Backup integrity check failed"
fi

log "Redis backup process completed successfully."