# 🚀 AgentsFlowAI VPS Quick Start Guide

This guide provides the fastest way to deploy PixelCraft Bloom on your VPS using the automated deployment script.

## 📋 Prerequisites

1. **VPS Server** - Ubuntu 22.04 LTS recommended (4 vCPUs, 16GB RAM)
2. **Domain Name** - `agentsflow.cloud` (already secured)
3. **SSH Access** - Root or sudo access to your server
4. **GitHub Account** - For CI/CD pipeline (optional)

## 🎯 Quick Deployment (5 Minutes)

### 1. Connect to Your VPS

```bash
ssh root@your-server-ip
```

### 2. Download and Run Deployment Script

```bash
# Download the deployment script
wget https://raw.githubusercontent.com/your-username/pixelcraft-bloom/main/ops/vps-deploy.sh
chmod +x vps-deploy.sh

# Run the script (this will take 5-10 minutes)
sudo ./vps-deploy.sh
```

### 3. Configure DNS

After deployment completes, configure your DNS:

```
A record: agentsflow.cloud → your-server-ip
A record: api.agentsflow.cloud → your-server-ip
```

## 📝 Post-Deployment Checklist

### 1. Update Environment Variables

```bash
nano /opt/pixelcraft-bloom/backend/.env
```

Update these critical values:
```env
# Database
SUPABASE__URL=postgresql://user:password@host:port/database
SUPABASE__KEY=your-service-role-key
SUPABASE__JWT_SECRET=your-jwt-secret

# Security
JWT_SECRET=your-strong-secret-here
BACKUP_ENCRYPTION_KEY=your-encryption-key-here
```

### 2. Restart Services

```bash
cd /opt/pixelcraft-bloom
docker compose down
docker compose up -d
```

### 3. Verify Deployment

```bash
# Check service status
docker compose ps

# Test API endpoints
curl https://api.agentsflow.cloud/health
curl https://api.agentsflow.cloud/api/models

# View logs
tail -f /var/log/pixelcraft/deploy.log
```

## 🔧 Common Commands

### Service Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View service logs
docker compose logs -f

# Restart specific service
docker compose restart backend
```

### Backup Management

```bash
# Run manual backup
sudo /opt/pixelcraft-bloom/ops/backup.sh

# List backups
ls -la /var/backups/pixelcraft/

# Restore backup
sudo /opt/pixelcraft-bloom/ops/restore.sh /var/backups/pixelcraft/backup_FILE.sql.gz.gpg
```

### Monitoring

```bash
# Check system resources
htop

# View nginx status
systemctl status nginx

# Check fail2ban
fail2ban-client status

# View firewall status
sudo ufw status
```

## 🆘 Troubleshooting

### API Not Responding

```bash
# Check nginx
systemctl status nginx
nginx -t

# Check docker containers
docker compose ps
docker compose logs backend

# Test backend directly
curl http://localhost:8000/health
```

### SSL Issues

```bash
# Check certificates
sudo certbot certificates

# Renew certificates
sudo certbot renew

# Test nginx config
sudo nginx -t
sudo systemctl reload nginx
```

### Database Connection Errors

```bash
# Test database connection
psql "your-connection-string" -c "SELECT 1;"

# Check connection pool
python -c "from backend.app.database import engine; print(engine.pool.status())"
```

## 📊 Performance Monitoring

```bash
# Check API response time
curl -s -o /dev/null -w "Time: %{time_total}s\n" https://api.agentsflow.cloud/health

# Monitor Redis
redis-cli info

# Check system load
uptime
free -h
df -h
```

## 🔄 Update Process

```bash
# Pull latest changes
cd /opt/pixelcraft-bloom
git pull origin main

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Verify update
curl https://api.agentsflow.cloud/health
```

## 🎉 Success Criteria

Your deployment is successful when:

✅ `docker compose ps` shows all containers "Up"
✅ `curl https://api.agentsflow.cloud/health` returns 200 OK
✅ `curl https://api.agentsflow.cloud/api/models` shows model data
✅ Browser shows lock icon (SSL working)
✅ No errors in `/var/log/pixelcraft/*.log`

## 📚 Quick Reference

| Task | Command |
|------|---------|
| **Deploy** | `sudo ./vps-deploy.sh` |
| **Start** | `docker compose up -d` |
| **Stop** | `docker compose down` |
| **Logs** | `docker compose logs -f` |
| **Backup** | `sudo ops/backup.sh` |
| **Restore** | `sudo ops/restore.sh backup_file` |
| **Health** | `curl https://api.agentsflow.cloud/health` |
| **Docs** | `https://api.agentsflow.cloud/docs` |

## 🚀 Next Steps

1. **Deploy Frontend** - Update frontend to use `https://api.agentsflow.cloud`
2. **Monitor** - Set up monitoring dashboard
3. **Scale** - Add load balancer when traffic increases
4. **Optimize** - Implement caching and performance tuning
5. **Secure** - Set up firewall rules and security updates

---

**Congratulations!** 🎉 Your PixelCraft Bloom backend is now deployed and ready for production use.

**Production URL:** https://api.agentsflow.cloud
**Documentation:** https://api.agentsflow.cloud/docs
**Health Check:** https://api.agentsflow.cloud/health