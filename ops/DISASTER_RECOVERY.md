# Disaster Recovery Runbook

This document outlines the procedures for database backup and recovery for AgentsFlowAI.

## Backup Strategy

- **Frequency**: Daily at 02:00 UTC.
- **Retention**: 30 days.
- **Method**: `pg_dump` of the Supabase database.
- **Security**: Backups are compressed (`gzip`) and symmetrically encrypted (`gpg` AES256) before storage.
- **Storage**: Local VPS storage at `/var/backups/agentsflowai`. (Recommendation: Sync this directory to S3/R2 for offsite storage).

## Configuration

The following environment variables in `/opt/agentsflowai/backend/.env` are required:

- `SUPABASE_DB_URL`: The PostgreSQL connection string (Transaction pooler or Session pooler).
- `BACKUP_ENCRYPTION_KEY`: A strong passphrase used to encrypt the backup files.

## Automated Backups

Backups are automated via cron. The setup script `ops/setup-backups.sh` configures the cron job.

To verify the cron job:
```bash
crontab -l
```

To manually trigger a backup:
```bash
sudo /opt/agentsflowai/ops/backup.sh
```

## Recovery Procedures

### Point-in-Time Recovery (PITR)

Since we are using Supabase, PITR is managed by the Supabase platform (if enabled on the Pro plan).
1. Go to the Supabase Dashboard > Database > Backups.
2. Select the point in time to restore to.
3. Follow the Supabase instructions to restore the project.

### Manual Restore from Backup File

If you need to restore from one of our daily offsite/local backups (e.g., catastrophic failure of Supabase project or accidental deletion not covered by PITR window):

1. **Locate the Backup**:
   Find the desired backup file in `/var/backups/agentsflowai`.
   ```bash
   ls -lh /var/backups/agentsflowai
   ```

2. **Run Restore Script**:
   Use the `restore.sh` script. **WARNING**: This will overwrite the current database.
   ```bash
   sudo /opt/agentsflowai/ops/restore.sh /var/backups/agentsflowai/backup_YYYYMMDD_HHMMSS.sql.gz.gpg
   ```

3. **Verify Data**:
   Check the application or database to ensure data integrity.

## Testing Recovery

It is recommended to test the recovery process monthly:
1. Create a fresh Supabase project or local Postgres instance.
2. Configure `.env` with the test database URL.
3. Run the restore script against the test database.
4. Verify the application works with the restored data.
