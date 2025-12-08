#!/bin/bash
set -e

# Install dependencies
echo "Installing PostgreSQL client tools and GPG..."
apt-get update
apt-get install -y postgresql-client gnupg

# Create backup directory
mkdir -p /var/backups/pixelcraft
mkdir -p /var/log/pixelcraft

# Set permissions
chmod +x /opt/pixelcraft-bloom/ops/backup.sh
chmod +x /opt/pixelcraft-bloom/ops/restore.sh
chmod +x /opt/pixelcraft-bloom/ops/backup-redis.sh
chmod +x /opt/pixelcraft-bloom/ops/monitor-backups.sh

# Setup Cron Jobs
# Database backup: Daily at 2 AM
DB_CRON_CMD="/opt/pixelcraft-bloom/ops/backup.sh >> /var/log/pixelcraft/backup.log 2>&1"
DB_JOB="0 2 * * * $DB_CRON_CMD"

# Redis backup: Daily at 2:30 AM
REDIS_CRON_CMD="/opt/pixelcraft-bloom/ops/backup-redis.sh >> /var/log/pixelcraft/redis-backup.log 2>&1"
REDIS_JOB="30 2 * * * $REDIS_CRON_CMD"

# Backup monitoring: Every 6 hours
MONITOR_CRON_CMD="/opt/pixelcraft-bloom/ops/monitor-backups.sh >> /var/log/pixelcraft/backup-monitor.log 2>&1"
MONITOR_JOB="0 */6 * * * $MONITOR_CRON_CMD"

if crontab -l | grep -q "pixelcraft-bloom/ops/backup.sh"; then
    echo "Cron job already exists."
else
    (crontab -l 2>/dev/null; echo "$JOB") | crontab -
    echo "Cron job added: $JOB"
fi

echo "Comprehensive backup setup complete."
echo "Scheduled jobs:"
echo "  - Database backup: Daily at 2:00 AM"
echo "  - Redis backup: Daily at 2:30 AM"
echo "  - Backup monitoring: Every 6 hours"
echo ""
echo "Logs are available in /var/log/pixelcraft/"
echo "Backups are stored in /var/backups/pixelcraft/"
