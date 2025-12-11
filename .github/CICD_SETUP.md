# AgentsFlowAI CI/CD Pipeline Setup

This guide explains how to set up the CI/CD pipeline for AgentsFlowAI using GitHub Actions.

## 🎯 Overview

The CI/CD pipeline includes:
- **Testing**: Automated backend tests with PostgreSQL and Redis
- **Building**: Docker image creation and push to GitHub Container Registry
- **Deployment**: Production deployment via SSH
- **Monitoring**: Post-deployment health checks
- **GitHub Pages**: Frontend deployment for documentation
- **Documentation**: Automatic README updates

## 🚀 Setup Instructions

### 1. Configure GitHub Secrets

Go to your repository **Settings > Secrets > Actions** and add the following secrets:

#### Required Secrets:
- `SSH_PRIVATE_KEY` - Private SSH key for server access
- `SSH_USER` - SSH username (e.g., `root` or `agentsflowai`)
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
sudo adduser agentsflowai
sudo usermod -aG sudo agentsflowai
sudo usermod -aG docker agentsflowai

# Set up SSH key authentication
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Add your public key to authorized_keys
echo "your-public-key-here" >> ~/.ssh/authorized_keys

# Test SSH access
ssh agentsflowai@your-server-ip
```

### 3. Prepare Production Server

```bash
# Install required dependencies
sudo apt update
sudo apt install -y docker.io docker-compose git nginx certbot python3-certbot-nginx postgresql-client redis-tools gnupg

# Clone repository
git clone https://github.com/your-username/agentsflowai.git /opt/agentsflowai
cd /opt/agentsflowai

# Create directories
sudo mkdir -p /var/backups/agentsflowai
sudo mkdir -p /var/log/agentsflowai
sudo chown -R agentsflowai:agentsflowai /var/backups/agentsflowai
sudo chown -R agentsflowai:agentsflowai /var/log/agentsflowai
```

### 4. Configure Environment Variables

Create `/opt/agentsflowai/backend/.env` with the following content:

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
cd /opt/agentsflowai
sudo ./ops/deploy-production.sh
```

### 6. Start Services

```bash
cd /opt/agentsflowai
docker compose up -d
```

## 📊 Pipeline Workflow

The CI/CD pipeline consists of 6 jobs:

### 1. Test Job
- Runs on every push and pull request
- Executes backend tests with PostgreSQL and Redis services
- Generates code coverage reports
- Validates code quality

### 2. Build Job
- Runs after tests pass
- Builds Docker image and pushes to GitHub Container Registry
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

### 5. GitHub Pages Job
- Builds frontend for documentation
- Deploys to GitHub Pages
- Makes app viewable at `https://username.github.io/agentsflowai/`
- Updates automatically on each push

### 6. Documentation Job
- Updates README with GitHub Pages URL
- Commits documentation updates
- Ensures URLs are always current

## 🎯 Manual Deployment

To trigger a manual deployment:

```bash
# From your local machine
git checkout main
git pull origin main
git push origin main
```

## 📊 Monitoring and Maintenance

### View Deployment Logs

```bash
# On production server
tail -f /var/log/agentsflowai/deploy.log
tail -f /var/log/agentsflowai/backup.log
tail -f /var/log/agentsflowai/ssl-monitor.log
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

## 🔐 Security Best Practices

1. **Rotate secrets regularly** (every 90 days)
2. **Use strong encryption keys** (32+ characters)
3. **Restrict SSH access** with firewall rules
4. **Enable GitHub branch protection** for main branch
5. **Review deployment logs** for suspicious activity

## 📈 Performance Optimization

The pipeline includes basic performance monitoring. For advanced optimization:

1. **Add caching** to CI jobs
2. **Implement parallel testing**
3. **Use build matrix** for different environments
4. **Add load testing** to monitor job
5. **Optimize Docker layers** for faster builds

## 🔄 Rollback Procedure

```bash
# Find previous commit
git log --oneline -10

# Checkout previous version
git checkout previous-commit-hash

# Redeploy
sudo ./ops/deploy-production.sh
docker compose up -d

# Verify rollback
curl https://api.agentsflow.cloud/health
```

## 📋 Maintenance Checklist

### Daily Tasks
- [ ] Check health endpoints
- [ ] Review error logs
- [ ] Monitor rate limit hits
- [ ] Verify backup completion

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Check disk space usage
- [ ] Update dependencies
- [ ] Test backup restore procedure

### Monthly Tasks
- [ ] Full disaster recovery drill
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Capacity planning update

## 🎉 Success Criteria

Your deployment is successful when:

✅ **All Docker containers are running** (`docker compose ps`)
✅ **Health endpoint returns 200 OK** (`curl https://api.agentsflow.cloud/health`)
✅ **Models endpoint shows `"health": true`** (`curl https://api.agentsflow.cloud/api/models`)
✅ **SSL certificate is valid** (lock icon in browser)
✅ **Swagger UI is accessible** (`https://api.agentsflow.cloud/docs`)
✅ **No errors in logs** (`tail -f /var/log/agentsflowai/*.log`)
✅ **Backups are running** (`ls -la /var/backups/agentsflowai/`)
✅ **Monitoring is active** (`crontab -l`)
✅ **GitHub Pages is deployed** (`https://username.github.io/agentsflowai/`)

## 📚 Additional Resources

- **Hostinger Deployment Guide**: `HOSTINGER_DEPLOYMENT_GUIDE.md`
- **Production Readiness**: `ops/PRODUCTION_READINESS_COMPLETE.md`
- **Quick Reference**: `DEPLOYMENT_QUICK_REFERENCE.md`
- **Testing Instructions**: `TESTING_INSTRUCTIONS.md`

## 🆘 Support

For deployment issues:

1. **Check logs** in `/var/log/agentsflowai/`
2. **Review documentation** in this guide
3. **Test components individually** (database, Redis, API)
4. **Consult error messages** for specific troubleshooting steps
5. **Contact support** if issues persist

---

**Congratulations!** 🎉 Your AgentsFlowAI backend is now deployed and ready for production use.

**Next Steps:**
1. Deploy frontend application
2. Update frontend API URLs to use `https://api.agentsflow.cloud`
3. Test complete application end-to-end
4. Monitor performance and optimize as needed
5. Set up user analytics and error tracking

**Production URL:** https://api.agentsflow.cloud
**Documentation:** https://api.agentsflow.cloud/docs
**Health Check:** https://api.agentsflow.cloud/health
**GitHub Pages:** https://username.github.io/agentsflowai/