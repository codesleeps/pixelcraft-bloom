#!/bin/bash
# PixelCraft Database Restore Script
# Usage: ./restore-db.sh <backup_file>

set -e  # Exit on any error

# Check arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 ./backups/pixelcraft_db_20231201_020000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file '$BACKUP_FILE' does not exist"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$SUPABASE_URL" ]; then
    echo "ERROR: SUPABASE_URL environment variable not set"
    exit 1
fi

echo "Starting database restore from: $BACKUP_FILE"

# Confirm action
read -p "This will overwrite the current database. Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Perform restore
echo "Restoring database..."
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql "$SUPABASE_URL"
else
    psql "$SUPABASE_URL" < "$BACKUP_FILE"
fi

echo "Database restore completed successfully!"
