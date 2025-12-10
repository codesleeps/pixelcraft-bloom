#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/var/backups/agentsflowai"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"
ENCRYPTED_FILE="$BACKUP_FILE.gpg"
LOG_FILE="/var/log/agentsflowai/backup.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Load environment variables
if [ -f "/opt/pixelcraft-bloom/backend/.env" ]; then
    source "/opt/pixelcraft-bloom/backend/.env"
else
    echo "Error: .env file not found"
    exit 1
fi

# Check required variables
if [ -z "$SUPABASE_DB_URL" ]; then
    echo "Error: SUPABASE_DB_URL not set in .env"
    exit 1
fi

if [ -z "$BACKUP_ENCRYPTION_KEY" ]; then
    echo "Error: BACKUP_ENCRYPTION_KEY not set in .env"
    exit 1
fi

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting backup..."

# 1. Dump database
# Using pg_dump with the connection string
if pg_dump "$SUPABASE_DB_URL" | gzip > "$BACKUP_FILE"; then
    log "Database dump successful: $BACKUP_FILE"
else
    log "Error: Database dump failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# 2. Encrypt backup
if gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --symmetric --cipher-algo AES256 -o "$ENCRYPTED_FILE" "$BACKUP_FILE"; then
    log "Encryption successful: $ENCRYPTED_FILE"
    # Remove unencrypted file
    rm -f "$BACKUP_FILE"
else
    log "Error: Encryption failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# 3. Cleanup old backups
log "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "backup_*.sql.gz.gpg" -mtime +$RETENTION_DAYS -delete

log "Backup process completed successfully."
