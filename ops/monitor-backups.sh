#!/bin/bash

BACKUP_DIR="/var/backups/agentsflowai"
LOG_FILE="/var/log/agentsflowai/backup-monitor.log"
ALERT_EMAIL="${ALERT_EMAIL:-admin@agentsflow.cloud}"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    local message="$1"
    log "ALERT: $message"

    # Send email alert if mail is available
    if command -v mail >/dev/null 2>&1 && [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "PixelCraft Backup Alert" "$ALERT_EMAIL"
    fi

    # Here you could integrate with other notification systems
    # like Slack, Discord, or monitoring services
}

log "Starting backup monitoring check..."

# Check if latest database backup is less than 25 hours old
LATEST_DB_BACKUP=$(find "$BACKUP_DIR" -name "backup_*.sql.gz.gpg" -mtime -1 2>/dev/null | wc -l)
if [ "$LATEST_DB_BACKUP" -eq 0 ]; then
    alert "No recent database backup found (older than 24 hours)!"
else
    log "Database backup check passed: $LATEST_DB_BACKUP recent backup(s) found"
fi

# Check if latest Redis backup is less than 25 hours old
LATEST_REDIS_BACKUP=$(find "$BACKUP_DIR" -name "redis_*.rdb.gz.gpg" -mtime -1 2>/dev/null | wc -l)
if [ "$LATEST_REDIS_BACKUP" -eq 0 ]; then
    alert "No recent Redis backup found (older than 24 hours)!"
else
    log "Redis backup check passed: $LATEST_REDIS_BACKUP recent backup(s) found"
fi

# Check backup directory exists and is accessible
if [ ! -d "$BACKUP_DIR" ]; then
    alert "Backup directory $BACKUP_DIR does not exist!"
elif [ ! -w "$BACKUP_DIR" ]; then
    alert "Backup directory $BACKUP_DIR is not writable!"
else
    log "Backup directory check passed"
fi

# Check disk space usage
if [ -d "$BACKUP_DIR" ]; then
    DISK_USAGE=$(df "$BACKUP_DIR" 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ -n "$DISK_USAGE" ] && [ "$DISK_USAGE" -gt 90 ]; then
        alert "Backup disk usage is ${DISK_USAGE}% - consider cleanup or expansion"
    elif [ -n "$DISK_USAGE" ] && [ "$DISK_USAGE" -gt 80 ]; then
        log "Warning: Backup disk usage is ${DISK_USAGE}%"
    else
        log "Disk usage check passed: ${DISK_USAGE}%"
    fi
fi

# Check backup file integrity (sample check on latest files)
LATEST_DB_FILE=$(find "$BACKUP_DIR" -name "backup_*.sql.gz.gpg" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
if [ -n "$LATEST_DB_FILE" ] && [ -f "$LATEST_DB_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$LATEST_DB_FILE" 2>/dev/null || stat -c%s "$LATEST_DB_FILE" 2>/dev/null)
    if [ "$FILE_SIZE" -gt 1000 ]; then  # At least 1KB
        log "Database backup file integrity check passed: $LATEST_DB_FILE (${FILE_SIZE} bytes)"
    else
        alert "Database backup file appears too small: $LATEST_DB_FILE (${FILE_SIZE} bytes)"
    fi
fi

LATEST_REDIS_FILE=$(find "$BACKUP_DIR" -name "redis_*.rdb.gz.gpg" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
if [ -n "$LATEST_REDIS_FILE" ] && [ -f "$LATEST_REDIS_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$LATEST_REDIS_FILE" 2>/dev/null || stat -c%s "$LATEST_REDIS_FILE" 2>/dev/null)
    if [ "$FILE_SIZE" -gt 100 ]; then  # At least 100 bytes
        log "Redis backup file integrity check passed: $LATEST_REDIS_FILE (${FILE_SIZE} bytes)"
    else
        alert "Redis backup file appears too small: $LATEST_REDIS_FILE (${FILE_SIZE} bytes)"
    fi
fi

# Count total backups for reporting
DB_BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz.gpg" 2>/dev/null | wc -l)
REDIS_BACKUP_COUNT=$(find "$BACKUP_DIR" -name "redis_*.rdb.gz.gpg" 2>/dev/null | wc -l)

log "Backup monitoring completed. Total backups - DB: $DB_BACKUP_COUNT, Redis: $REDIS_BACKUP_COUNT"