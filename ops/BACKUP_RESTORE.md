# Backup & Restore Procedures

This document outlines the backup and restore procedures for AgentsFlowAI production environment, covering both database and Redis cache backups.

## Overview

The backup strategy includes:
- **Database**: Daily automated PostgreSQL dumps using `pg_dump`
- **Redis**: RDB snapshots with configurable retention
- **Encryption**: All backups are encrypted using GPG
- **Automation**: Cron-based scheduling for daily backups
- **Retention**: 30-day retention policy with automatic cleanup

## Prerequisites

### Environment Variables
Ensure the following variables are set in `/opt/agentsflowai/backend/.env`:

```bash
SUPABASE_DB_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://host:port/db
BACKUP_ENCRYPTION_KEY=your-strong-encryption-key-here
```

### System Dependencies
```bash
# Install required packages
sudo apt-get update
sudo apt-get install -y postgresql-client redis-tools gnupg cron
```

## Database Backup

### Automated Daily Backup

The system is configured for daily automated backups at 2:00 AM via cron.

#### Setup Automation
```bash
# Run setup script
sudo ./ops/setup-backups.sh

# Verify cron job
crontab -l | grep backup
```

#### Manual Backup
```bash
# Execute backup manually
sudo ./ops/backup.sh

# Check logs
tail -f /var/log/agentsflowai/backup.log
```

### Backup Process Details

1. **Database Dump**: Uses `pg_dump` to create a compressed SQL dump
2. **Compression**: Gzip compression to reduce storage space
3. **Encryption**: AES256 encryption using GPG
4. **Storage**: Saves to `/var/backups/agentsflowai/`
5. **Cleanup**: Removes backups older than 30 days

### Backup File Naming
```
backup_YYYYMMDD_HHMMSS.sql.gz.gpg
```

## Redis Backup

### Redis Configuration

Ensure Redis is configured for persistence in `/etc/redis/redis.conf`:

```ini
# Enable RDB snapshots
save 900 1      # Save after 900 seconds if at least 1 key changed
save 300 10     # Save after 300 seconds if at least 10 keys changed
save 60 10000   # Save after 60 seconds if at least 10000 keys changed

# RDB file location
dbfilename dump.rdb
dir /var/lib/redis

# Optional: Enable AOF for additional durability
appendonly yes
appendfilename "appendonly.aof"
```

### Redis Backup Strategy

#### RDB Snapshots (Primary)
```bash
# Manual RDB backup
redis-cli -u "$REDIS_URL" --rdb /var/backups/agentsflowai/redis_$(date +%Y%m%d_%H%M%S).rdb

# With compression and encryption
redis-cli -u "$REDIS_URL" --rdb - | gzip | gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --symmetric --cipher-algo AES256 -o /var/backups/agentsflowai/redis_$(date +%Y%m%d_%H%M%S).rdb.gz.gpg -
```

#### AOF Backup (Secondary)
```bash
# Copy AOF file if enabled
cp /var/lib/redis/appendonly.aof /var/backups/agentsflowai/redis_aof_$(date +%Y%m%d_%H%M%S).aof
gzip /var/backups/agentsflowai/redis_aof_$(date +%Y%m%d_%H%M%S).aof
```

### Automated Redis Backup Script

Create `/opt/agentsflowai/ops/backup-redis.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/agentsflowai"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/agentsflowai/redis-backup.log"

# Load environment
source "/opt/agentsflowai/backend/.env"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Redis backup..."

# RDB Backup
RDB_FILE="$BACKUP_DIR/redis_$DATE.rdb.gz.gpg"
redis-cli -u "$REDIS_URL" --rdb - | gzip | gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --symmetric --cipher-algo AES256 -o "$RDB_FILE"

log "Redis RDB backup completed: $RDB_FILE"

# Cleanup old Redis backups (30 days)
find "$BACKUP_DIR" -name "redis_*.rdb.gz.gpg" -mtime +30 -delete

log "Redis backup process completed."
```

## Restore Procedures

### Database Restore

#### Full Database Restore
```bash
# List available backups
ls -lh /var/backups/agentsflowai/backup_*.sql.gz.gpg

# Restore from specific backup
sudo ./ops/restore.sh /var/backups/agentsflowai/backup_20231201_020000.sql.gz.gpg

# Check logs
tail -f /var/log/agentsflowai/restore.log
```

#### Point-in-Time Recovery
For Supabase hosted databases, use their point-in-time recovery features through the dashboard.

### Redis Restore

#### RDB Restore
```bash
# Stop Redis service
sudo systemctl stop redis-server

# Backup current RDB file
cp /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.backup

# Decrypt and restore RDB file
gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --decrypt /var/backups/agentsflowai/redis_20231201_020000.rdb.gz.gpg | gunzip > /var/lib/redis/dump.rdb

# Set proper permissions
chown redis:redis /var/lib/redis/dump.rdb

# Start Redis service
sudo systemctl start redis-server
```

#### AOF Restore (if applicable)
```bash
# Stop Redis
sudo systemctl stop redis-server

# Restore AOF file
gunzip -c /var/backups/agentsflowai/redis_aof_20231201_020000.aof.gz > /var/lib/redis/appendonly.aof
chown redis:redis /var/lib/redis/appendonly.aof

# Start Redis
sudo systemctl start redis-server
```

## Verification Steps

### Database Verification
```bash
# Connect to database
psql "$SUPABASE_DB_URL" -c "SELECT COUNT(*) FROM users;"

# Check table integrity
psql "$SUPABASE_DB_URL" -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';"

# Verify recent data
psql "$SUPABASE_DB_URL" -c "SELECT created_at FROM conversations ORDER BY created_at DESC LIMIT 5;"
```

### Redis Verification
```bash
# Check Redis connectivity
redis-cli -u "$REDIS_URL" ping

# Verify key count
redis-cli -u "$REDIS_URL" dbsize

# Check specific keys
redis-cli -u "$REDIS_URL" keys "*"

# Verify cache functionality
redis-cli -u "$REDIS_URL" get "some:known:key"
```

### Backup Integrity Check
```bash
# Test database backup decryption
gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --decrypt /var/backups/agentsflowai/backup_20231201_020000.sql.gz.gpg | gunzip | head -20

# Test Redis backup decryption
gpg --batch --yes --passphrase "$BACKUP_ENCRYPTION_KEY" --decrypt /var/backups/agentsflowai/redis_20231201_020000.rdb.gz.gpg | gunzip | head -c 100
```

## Monitoring & Alerts

### Backup Monitoring
```bash
# Check backup success
ls -la /var/backups/agentsflowai/ | tail -5

# Monitor backup logs
tail -50 /var/log/agentsflowai/backup.log

# Check disk space
df -h /var/backups
```

### Automated Monitoring Script
Create `/opt/agentsflowai/ops/monitor-backups.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/agentsflowai"
LOG_FILE="/var/log/agentsflowai/backup-monitor.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if latest backup is less than 25 hours old
LATEST_BACKUP=$(find "$BACKUP_DIR" -name "backup_*.sql.gz.gpg" -mtime -1 | wc -l)
if [ "$LATEST_BACKUP" -eq 0 ]; then
    log "WARNING: No recent database backup found!"
    # Send alert (integrate with your notification system)
fi

LATEST_REDIS=$(find "$BACKUP_DIR" -name "redis_*.rdb.gz.gpg" -mtime -1 | wc -l)
if [ "$LATEST_REDIS" -eq 0 ]; then
    log "WARNING: No recent Redis backup found!"
    # Send alert
fi

# Check disk space
DISK_USAGE=$(df "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log "WARNING: Backup disk usage is ${DISK_USAGE}%"
fi

log "Backup monitoring completed."
```

## Disaster Recovery

### Complete System Recovery

1. **Provision new server** with same specifications
2. **Install dependencies** and application code
3. **Restore database** from latest backup
4. **Restore Redis cache** from latest backup
5. **Update DNS** to point to new server
6. **Verify functionality** using health checks

### Recovery Time Objectives (RTO)
- **Database**: 1-2 hours for full restore
- **Redis**: 15-30 minutes for cache warm-up
- **Full System**: 2-4 hours including verification

### Recovery Point Objectives (RPO)
- **Database**: Up to 24 hours (daily backups)
- **Redis**: Up to 15 minutes (RDB snapshots)

## Security Considerations

- **Encryption**: All backups are encrypted at rest
- **Access Control**: Backup files stored with restricted permissions
- **Network Security**: Database connections use SSL/TLS
- **Key Management**: Encryption keys stored securely in environment variables
- **Audit Logging**: All backup and restore operations are logged

## Maintenance

### Regular Tasks
- **Monthly**: Test restore procedures on staging environment
- **Quarterly**: Review and update backup retention policies
- **Annually**: Full disaster recovery drill

### Storage Management
- Monitor backup storage usage
- Implement offsite backup replication if required
- Regular cleanup of expired backups

## Troubleshooting

### Common Issues

**Backup fails with permission error:**
```bash
# Check directory permissions
ls -ld /var/backups/agentsflowai
sudo chown -R backupuser:backupuser /var/backups/agentsflowai
```

**Database connection fails:**
```bash
# Test connection
psql "$SUPABASE_DB_URL" -c "SELECT 1;"
# Check environment variables
echo $SUPABASE_DB_URL
```

**Redis backup fails:**
```bash
# Check Redis connectivity
redis-cli -u "$REDIS_URL" ping
# Verify Redis configuration
redis-cli -u "$REDIS_URL" config get save
```

**Decryption fails:**
```bash
# Verify encryption key
echo $BACKUP_ENCRYPTION_KEY
# Test decryption manually
gpg --batch --passphrase "$BACKUP_ENCRYPTION_KEY" --decrypt test_file.gpg