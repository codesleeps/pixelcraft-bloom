# PixelCraft Bloom CI/CD Pipeline Setup

This guide explains how to set up the CI/CD pipeline for PixelCraft Bloom using GitHub Actions.

## Prerequisites

1. GitHub repository with admin access
2. Production server with SSH access
3. Domain name configured (agentsflow.cloud)
4. Docker and Docker Compose installed on production server

## Setup Instructions

### 1. Configure GitHub Secrets

Go to your repository **Settings > Secrets > Actions** and add the following secrets:

#### Required Secrets:
- `SSH_PRIVATE_KEY` - Private SSH key for server access
- `SSH_USER` - SSH username (e.g., `root` or `pixelcraft`)
- `SSH_HOST` - Server IP address or hostname
- `KNOWN_HOSTS` - Server's SSH host key (run `ssh-keyscan your-server-ip`)
- `SUPABASE_URL` - Production Supabase database URL
- `SUPABASE_KEY` - Production Supabase service role key
- `SUPABASE_JWT_SECRET` - Production Supabase JWT secret
- `REDIS_URL` - Production Redis connection URL
- `BACKUP_ENCRYPTION_KEY` - Strong encryption key for backups

#### Optional Secrets:
- `SLACK_WEBHOOK` - Slack webhook URL for deployment notifications
- `GITHUB_TOKEN` - GitHub token for container registry (automatically provided)

### 2. Set Up SSH Access

On your production server:

```bash
# Create user if needed
sudo adduser pixelcraft
sudo usermod -aG sudo pixelcraft
sudo usermod -aG docker pixelcraft

# Set up SSH key authentication
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Add your public key to authorized_keys
echo "your-public-key-here" >> ~/.ssh/authorized_keys

# Test SSH access
ssh pixelcraft@your-server-ip
```

### 3. Prepare Production Server

```bash
# Install required dependencies
sudo apt update
sudo apt install -y docker.io docker-compose git nginx certbot python3-certbot-nginx postgresql-client redis-tools gnupg

# Clone repository
git clone https://github.com/your-username/pixelcraft-bloom.git /opt/pixelcraft-bloom
cd /opt/pixelcraft-bloom

# Create directories
sudo mkdir -p /var/backups/pixelcraft
sudo mkdir -p /var/log/pixelcraft
sudo chown -R pixelcraft:pixelcraft /var/backups/pixelcraft
sudo chown -R pixelcraft:pixelcraft /var/log/pixelcraft
```

### 4. Configure Environment Variables

Create `/opt/pixelcraft-bloom/backend/.env` with the following content:

```env
# Application
APP_ENV=production
LOG_LEVEL=INFO
USE_HTTPS=true

# Database
SUPABASE__URL=your-supabase-url
SUPABASE__KEY=your-supabase-key
SUPABASE__JWT_SECRET=your-supabase-jwt-secret

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
CORS_ORIGINS=https://agentsflow.cloud,https://www.agentsflow.cloud,https://api.agentsflow.cloud
JWT_SECRET=your-strong-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Backup
BACKUP_ENCRYPTION_KEY=your-strong-encryption-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production
```

### 5. Initial Deployment

Run the deployment script manually for the first time:

```bash
cd /opt/pixelcraft-bloom
sudo ./ops/deploy-production.sh
```

### 6. Start Services

```bash
cd /opt/pixelcraft-bloom
docker compose up -d
```

## Pipeline Workflow

The CI/CD pipeline consists of 5 jobs:

### 1. Test Job
- Runs on every push and pull request
- Executes backend tests with PostgreSQL and Redis services
- Generates code coverage reports
- Validates code quality

### 2. Build Job
- Runs after tests pass
- Builds Docker image with GitHub Container Registry
- Tags images with commit SHA and "latest"
- Uses Docker layer caching for faster builds

### 3. Deploy Job
- Runs only on main branch pushes
- Deploys to production server via SSH
- Updates environment variables
- Runs deployment script
- Restarts services
- Verifies deployment health

### 4. Monitor Job
- Runs post-deployment health checks
- Verifies API endpoints
- Tests performance
- Checks security headers
- Validates backup system

## Manual Deployment

To trigger a manual deployment:

```bash
# From your local machine
git checkout main
git pull origin main
git push origin main
```

## Monitoring and Maintenance

### View Deployment Logs

```bash
# On production server
tail -f /var/log/pixelcraft/deploy.log
tail -f /var/log/pixelcraft/backup.log
tail -f /var/log/pixelcraft/ssl-monitor.log
```

### Check Service Status

```bash
docker compose ps
systemctl status nginx
certbot certificates
```

### Troubleshooting

**Issue: Deployment fails with SSH connection error**
- Verify SSH key is correctly added to GitHub secrets
- Check server firewall allows SSH connections
- Test manual SSH connection

**Issue: Docker build fails**
- Check Dockerfile syntax
- Verify all required files are in repository
- Clean Docker cache: `docker system prune -a`

**Issue: Tests fail in CI**
- Run tests locally first
- Check database connection strings
- Verify test data setup

## Security Best Practices

1. **Rotate secrets regularly** (every 90 days)
2. **Use strong encryption keys** (32+ characters)
3. **Restrict SSH access** with firewall rules
4. **Enable GitHub branch protection** for main branch
5. **Review deployment logs** for suspicious activity

## Performance Optimization

The pipeline includes basic performance monitoring. For advanced optimization:

1. **Add caching** to CI jobs
2. **Implement parallel testing**
3. **Use build matrix** for different environments
4. **Add load testing** to monitor job
5. **Optimize Docker layers** for faster builds

## Backup and Recovery

The deployment script sets up automated backups:

- **Daily database backups** at 2:00 AM
- **Daily Redis backups** at 2:30 AM
- **30-day retention policy**
- **AES-256 encryption**

To restore from backup:

```bash
# List available backups
ls -la /var/backups/pixelcraft/

# Restore specific backup
sudo ./ops/restore.sh /var/backups/pixelcraft/backup_YYYYMMDD_HHMMSS.sql.gz.gpg
```

## Rollback Procedure

To rollback to previous version:

```bash
# Find previous commit
git log --oneline -5

# Checkout previous version
git checkout previous-commit-hash

# Redeploy
sudo ./ops/deploy-production.sh
docker compose up -d
```

## Cost Optimization

1. **Use GitHub Actions caching** for dependencies
2. **Limit concurrent workflows** in repository settings
3. **Use smaller runners** for test jobs
4. **Schedule non-critical jobs** during off-peak hours
5. **Clean up old artifacts** regularly