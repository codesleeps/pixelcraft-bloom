# AgentsFlowAI Production Deployment Guide

This comprehensive guide covers the complete deployment process for PixelCraft Bloom, from initial setup to production monitoring.

## 🎯 Overview

PixelCraft Bloom is now ready for production deployment with:
- ✅ **SSL Certificates**: Let's Encrypt with automatic renewal
- ✅ **Nginx Configuration**: HTTPS with security headers and rate limiting
- ✅ **Backup System**: Automated daily backups with 30-day retention
- ✅ **Monitoring**: SSL expiry and backup health checks
- ✅ **CI/CD Pipeline**: Automated testing and deployment

## 📋 Deployment Checklist

### Pre-Deployment Preparation

- [ ] Secure domain name (agentsflow.cloud)
- [ ] Set up production server (Ubuntu 22.04 LTS recommended)
- [ ] Configure DNS records for agentsflow.cloud and api.agentsflow.cloud
- [ ] Set up Supabase production database
- [ ] Configure Redis server
- [ ] Install required dependencies on server

### Deployment Steps

1. **Server Setup** - Install dependencies and configure environment
2. **SSL Configuration** - Set up Let's Encrypt certificates
3. **Nginx Configuration** - Configure HTTPS reverse proxy
4. **Backup System** - Set up automated backups
5. **Monitoring** - Configure health checks and alerts
6. **CI/CD Pipeline** - Set up automated deployment
7. **Final Verification** - Test all systems

## 🚀 Step-by-Step Deployment

### 1. Server Setup

```bash
# Connect to your server
ssh root@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y docker.io docker-compose git nginx certbot python3-certbot-nginx postgresql-client redis-tools gnupg

# Create user
sudo adduser pixelcraft
sudo usermod -aG sudo pixelcraft
sudo usermod -aG docker pixelcraft

# Clone repository
sudo mkdir -p /opt/pixelcraft-bloom
sudo chown pixelcraft:pixelcraft /opt/pixelcraft-bloom
git clone https://github.com/your-username/pixelcraft-bloom.git /opt/pixelcraft-bloom
```

### 2. Environment Configuration

Create `/opt/pixelcraft-bloom/backend/.env`:

```env
# Application
APP_ENV=production
LOG_LEVEL=INFO
USE_HTTPS=true

# Database
SUPABASE__URL=postgresql://postgres:your-password@localhost:5432/pixelcraft
SUPABASE__KEY=your-supabase-service-role-key
SUPABASE__JWT_SECRET=your-supabase-jwt-secret

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
CORS_ORIGINS=https://agentsflow.cloud,https://www.agentsflow.cloud,https://api.agentsflow.cloud
JWT_SECRET=your-strong-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Backup
BACKUP_ENCRYPTION_KEY=your-strong-encryption-key-here

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
SENTRY_ENVIRONMENT=production
```

### 3. Run Deployment Script

```bash
cd /opt/pixelcraft-bloom
sudo ./ops/deploy-production.sh
```

This script will:
- Set up SSL certificates with Let's Encrypt
- Configure Nginx for HTTPS
- Set up automated backups
- Configure monitoring
- Set up automatic certificate renewal

### 4. Start Services

```bash
cd /opt/pixelcraft-bloom
docker compose up -d
```

### 5. Verify Deployment

```bash
# Check service status
docker compose ps

# Test API endpoints
curl https://api.agentsflow.cloud/health
curl https://api.agentsflow.cloud/api/models

# Check logs
tail -f /var/log/pixelcraft/deploy.log
tail -f /var/log/nginx/access.log
```

## 🔐 Security Configuration

### SSL/TLS Security

The deployment includes:
- **TLS 1.2 and 1.3** only
- **Strong cipher suites**
- **HSTS header** (Strict-Transport-Security)
- **Automatic certificate renewal** every 90 days

### Security Headers

All responses include:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

### Rate Limiting

- **100 requests per minute** per user/IP
- **Burst capacity** of 20 requests
- **Connection limiting** (10 concurrent connections per IP)

## 💾 Backup and Recovery

### Backup Schedule

- **Database backups**: Daily at 2:00 AM
- **Redis backups**: Daily at 2:30 AM
- **Backup monitoring**: Every 6 hours
- **Retention**: 30 days

### Manual Backup

```bash
# Run manual backup
sudo /opt/pixelcraft-bloom/ops/backup.sh

# Check backup logs
tail -f /var/log/pixelcraft/backup.log
```

### Restore Process

```bash
# List available backups
ls -la /var/backups/pixelcraft/

# Restore specific backup
sudo /opt/pixelcraft-bloom/ops/restore.sh /var/backups/pixelcraft/backup_YYYYMMDD_HHMMSS.sql.gz.gpg
```

## 📊 Monitoring and Alerts

### Monitoring Setup

The deployment includes:
- **SSL certificate expiry monitoring** (daily)
- **Backup health monitoring** (every 6 hours)
- **Disk space monitoring**
- **Backup integrity checks**

### View Monitoring Logs

```bash
# SSL monitoring
tail -f /var/log/pixelcraft/ssl-monitor.log

# Backup monitoring
tail -f /var/log/pixelcraft/backup-monitor.log

# System logs
journalctl -u nginx -f
journalctl -u docker -f
```

## 🔄 CI/CD Pipeline

### Pipeline Overview

1. **Test Job**: Runs backend tests with PostgreSQL and Redis
2. **Build Job**: Builds Docker image and pushes to GitHub Container Registry
3. **Deploy Job**: Deploys to production server via SSH
4. **Monitor Job**: Verifies deployment health

### Trigger Deployment

```bash
# Push to main branch to trigger deployment
git checkout main
git commit -m "Update for deployment"
git push origin main
```

### Monitor Pipeline

1. Go to GitHub repository
2. Click on "Actions" tab
3. View workflow runs
4. Check deployment logs

## 🚨 Troubleshooting

### Common Issues

**Issue: SSL certificate not working**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew

# Test nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

**Issue: Database connection failed**
```bash
# Test database connection
psql "postgresql://user:password@host:port/database" -c "SELECT 1;"

# Check connection pooling
python -c "from backend.app.database import engine; print(engine.pool.status())"
```

**Issue: Redis connection failed**
```bash
# Test Redis connection
redis-cli -u "redis://localhost:6379/0" ping

# Check Redis status
sudo systemctl status redis-server
```

**Issue: Backup failed**
```bash
# Check backup logs
tail -50 /var/log/pixelcraft/backup.log

# Test manual backup
sudo /opt/pixelcraft-bloom/ops/backup.sh

# Check disk space
df -h /var/backups
```

## 📈 Performance Optimization

### Database Optimization

```bash
# Check database performance
psql "your-database-url" -c "SELECT * FROM pg_stat_activity;"

# Add indexes (example)
psql "your-database-url" -c "CREATE INDEX idx_conversations_user_id ON conversations(user_id);"
```

### Caching Strategies

```bash
# Configure Redis caching
# In backend/app/utils/cache.py

# Add caching decorators to API endpoints
@cache(ttl=300)  # 5 minute cache
async def get_popular_models():
    # Your implementation
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f backend/tests/load/locustfile.py --host=https://api.agentsflow.cloud
```

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
✅ **No errors in logs** (`tail -f /var/log/pixelcraft/*.log`)
✅ **Backups are running** (`ls -la /var/backups/pixelcraft/`)
✅ **Monitoring is active** (`crontab -l`)

## 📚 Additional Resources

- **Hostinger Deployment Guide**: `HOSTINGER_DEPLOYMENT_GUIDE.md`
- **Production Readiness**: `ops/PRODUCTION_READINESS_COMPLETE.md`
- **Quick Reference**: `DEPLOYMENT_QUICK_REFERENCE.md`
- **Testing Instructions**: `TESTING_INSTRUCTIONS.md`

## 🆘 Support

For deployment issues:

1. **Check logs** in `/var/log/pixelcraft/`
2. **Review documentation** in this guide
3. **Test components individually** (database, Redis, API)
4. **Consult error messages** for specific troubleshooting steps
5. **Contact support** if issues persist

---

**Congratulations!** 🎉 Your PixelCraft Bloom backend is now deployed and ready for production use.

**Next Steps:**
1. Deploy frontend application
2. Update frontend API URLs to use `https://api.agentsflow.cloud`
3. Test complete application end-to-end
4. Monitor performance and optimize as needed
5. Set up user analytics and error tracking

**Production URL:** https://api.agentsflow.cloud
**Documentation:** https://api.agentsflow.cloud/docs
**Health Check:** https://api.agentsflow.cloud/health