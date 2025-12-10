#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/var/backups/agentsflowai"
LOG_FILE="/var/log/agentsflowai/restore.log"

# Load environment variables
if [ -f "/opt/pixelcraft-bloom/backend/.env" ]; then
    source "/opt/pixelcraft-bloom/backend/.env"
else
    echo "Error: .env file not found"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file_path>"
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/*.gpg
    exit 1
fi

INPUT_FILE="$1"
DECRYPTED_FILE="${INPUT_FILE%.gpg}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File $INPUT_FILE not found"
    exit 1
fi

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting restore process from $INPUT_FILE..."

# 1. Decrypt
log "Decrypting backup..."
if gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --decrypt -o "$DECRYPTED_FILE" "$INPUT_FILE"; then
    log "Decryption successful: $DECRYPTED_FILE"
else
    log "Error: Decryption failed"
    exit 1
fi

# 2. Restore
log "Restoring to database..."
# WARNING: This will overwrite the current database
read -p "WARNING: This will overwrite the database at $SUPABASE_DB_URL. Are you sure? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Restore cancelled."
    rm -f "$DECRYPTED_FILE"
    exit 1
fi

if gunzip -c "$DECRYPTED_FILE" | psql "$SUPABASE_DB_URL"; then
    log "Database restore successful."
else
    log "Error: Database restore failed."
fi

# Cleanup
rm -f "$DECRYPTED_FILE"
log "Restore process completed."
