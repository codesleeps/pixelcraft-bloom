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

# Setup Cron Job (Daily at 2 AM)
CRON_CMD="/opt/pixelcraft-bloom/ops/backup.sh >> /var/log/pixelcraft/backup.log 2>&1"
JOB="0 2 * * * $CRON_CMD"

if crontab -l | grep -q "pixelcraft-bloom/ops/backup.sh"; then
    echo "Cron job already exists."
else
    (crontab -l 2>/dev/null; echo "$JOB") | crontab -
    echo "Cron job added: $JOB"
fi

echo "Backup setup complete."
