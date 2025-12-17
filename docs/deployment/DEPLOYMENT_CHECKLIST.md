# Hostinger VPS Deployment Checklist

**Quick Reference for Deployment**  
**Print this and check off as you go!**

---

## 📋 Pre-Deployment (Before You Start)

- [ ] Purchase Hostinger VPS 4 (4 vCPUs, 16GB RAM)
- [ ] Choose Ubuntu 22.04 LTS
- [ ] Select data center location
- [ ] Receive VPS IP and root password via email
- [ ] Have domain name ready
- [ ] Have Supabase credentials ready
- [ ] Have GitHub repository URL

---

## 🔧 Initial Server Setup (30 minutes)

- [ ] SSH into VPS: `ssh root@YOUR_VPS_IP`
- [ ] Update system: `apt update && apt upgrade -y`
- [ ] Create user: `adduser agentsflowai`
- [ ] Add to sudo: `usermod -aG sudo agentsflowai`
- [ ] Set up SSH keys (optional but recommended)
- [ ] Switch to new user: `su - agentsflowai`

---

## 📦 Install Software (20 minutes)

- [ ] Install Docker: `curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh`
- [ ] Add user to docker group: `sudo usermod -aG docker $USER && newgrp docker`
- [ ] Install Docker Compose: `sudo apt install docker-compose-plugin -y`
- [ ] Install Git: `sudo apt install git -y`
- [ ] Install Nginx: `sudo apt install nginx -y`
- [ ] Install Certbot: `sudo apt install certbot python3-certbot-nginx -y`
- [ ] Verify all: `docker --version && git --version && nginx -v`

---

## 🔒 Configure Firewall (5 minutes)

- [ ] Allow SSH: `sudo ufw allow 22/tcp`
- [ ] Allow HTTP: `sudo ufw allow 80/tcp`
- [ ] Allow HTTPS: `sudo ufw allow 443/tcp`
- [ ] Enable firewall: `sudo ufw enable`
- [ ] Check status: `sudo ufw status`

---

## 🚀 Deploy Application (30 minutes)

- [ ] Clone repo: `git clone https://github.com/YOUR_USERNAME/agentsflowai.git`
- [ ] Navigate: `cd agentsflowai`
- [ ] Copy env: `cp .env.example .env`
- [ ] Edit env: `nano .env`
  - [ ] Set `APP_ENV=production`
  - [ ] Set `SUPABASE__URL=...`
  - [ ] Set `SUPABASE__KEY=...`
  - [ ] Set `SUPABASE__JWT_SECRET=...`
  - [ ] Set `REDIS_URL=redis://redis:6379/0`
  - [ ] Set `OLLAMA_HOST=http://ollama:11434`
  - [ ] Set `CORS_ORIGINS=https://yourdomain.com`
- [ ] Start services: `docker compose up -d`
- [ ] Wait for startup (5-10 minutes)
- [ ] Check status: `docker compose ps`

---

## 🤖 Pull AI Models (20 minutes)

- [ ] Pull Mistral: `docker compose exec ollama ollama pull mistral:7b`
- [ ] Wait for download (10-15 minutes)
- [ ] Verify: `docker compose exec ollama ollama list`
- [ ] Optional: Pull Mixtral: `docker compose exec ollama ollama pull mixtral:8x7b`

---

## 🧪 Test Locally (5 minutes)

- [ ] Test health: `curl http://localhost:8000/health`
- [ ] Test models: `curl http://localhost:8000/api/models`
- [ ] Check logs: `docker compose logs backend`
- [ ] Verify no errors

---

## 🌐 Configure Domain (15 minutes)

### DNS Configuration
- [ ] Go to domain registrar
- [ ] Add A record: `@` → `YOUR_VPS_IP`
- [ ] Add A record: `api` → `YOUR_VPS_IP`
- [ ] Wait for propagation (5-30 minutes)
- [ ] Test: `nslookup api.yourdomain.com`

### Nginx Configuration
- [ ] Create config: `sudo nano /etc/nginx/sites-available/agentsflowai-backend`
- [ ] Copy configuration from guide
- [ ] Enable site: `sudo ln -s /etc/nginx/sites-available/agentsflowai-backend /etc/nginx/sites-enabled/`
- [ ] Test config: `sudo nginx -t`
- [ ] Reload: `sudo systemctl reload nginx`

---

## 🔐 Install SSL (10 minutes)

- [ ] Run Certbot: `sudo certbot --nginx -d api.yourdomain.com`
- [ ] Enter email address
- [ ] Agree to terms
- [ ] Choose redirect to HTTPS (option 2)
- [ ] Wait for certificate installation
- [ ] Test: `curl https://api.yourdomain.com/health`

---

## 💾 Set Up Backups (10 minutes)

- [ ] Create backup dir: `mkdir -p ~/backups`
- [ ] Create script: `nano ~/backup.sh`
- [ ] Copy backup script from guide
- [ ] Make executable: `chmod +x ~/backup.sh`
- [ ] Test: `~/backup.sh`
- [ ] Schedule cron: `crontab -e`
- [ ] Add: `0 2 * * * /home/agentsflowai/backup.sh >> /home/agentsflowai/backup.log 2>&1`

---

## 📊 Set Up Monitoring (10 minutes)

- [ ] Install htop: `sudo apt install htop -y`
- [ ] Install netdata: `bash <(curl -Ss https://my-netdata.io/kickstart.sh)`
- [ ] Configure log rotation
- [ ] Test monitoring: `htop`

---

## ✅ Final Verification (10 minutes)

### Test All Endpoints
- [ ] Health: `curl https://api.yourdomain.com/health`
- [ ] Models: `curl https://api.yourdomain.com/api/models`
- [ ] Specific model: `curl https://api.yourdomain.com/api/models/mistral`
- [ ] Swagger UI: Visit `https://api.yourdomain.com/docs`

### Check Services
- [ ] Docker: `docker compose ps` (all should be "Up")
- [ ] Nginx: `sudo systemctl status nginx` (should be "active")
- [ ] SSL: Check browser shows lock icon
- [ ] Logs: `docker compose logs --tail=50 backend` (no errors)

### Performance Test
- [ ] Install ab: `sudo apt install apache2-utils -y`
- [ ] Run test: `ab -n 100 -c 10 https://api.yourdomain.com/health`
- [ ] Should complete successfully

---

## 🎯 Post-Deployment Tasks

### Immediate (Today)
- [ ] Update frontend to use new API URL
- [ ] Test end-to-end functionality
- [ ] Monitor logs for first few hours
- [ ] Share API URL with team

### This Week
- [ ] Set up error tracking (Sentry)
- [ ] Configure monitoring alerts
- [ ] Test backup restoration
- [ ] Document any custom configurations

### This Month
- [ ] Review performance metrics
- [ ] Optimize based on usage
- [ ] Plan scaling if needed
- [ ] Review security settings

---

## 📝 Important Information to Save

```
VPS Details:
IP Address: _______________________
Root Password: _______________________
User: agentsflowai
User Password: _______________________

Domain:
Main: _______________________
API: api._______________________

Supabase:
URL: _______________________
Service Role Key: _______________________
JWT Secret: _______________________

Monitoring:
Netdata: http://YOUR_VPS_IP:19999
Logs: docker compose logs -f backend

Backup:
Location: ~/backups/
Schedule: Daily at 2 AM
Retention: 7 days
```

---

## 🆘 Quick Troubleshooting

### Can't connect to VPS
```bash
# Check SSH service
sudo systemctl status ssh
sudo systemctl restart ssh
```

### Docker not working
```bash
# Restart Docker
sudo systemctl restart docker
docker compose up -d
```

### Nginx 502 error
```bash
# Check backend
docker compose ps
docker compose logs backend
curl http://localhost:8000/health
```

### SSL issues
```bash
# Check DNS
nslookup api.yourdomain.com

# Retry certificate
sudo certbot --nginx -d api.yourdomain.com
```

### Out of space
```bash
# Clean Docker
docker system prune -a -f

# Remove old logs
sudo journalctl --vacuum-time=7d
```

---

## ✨ Success Criteria

Your deployment is successful when:

- ✅ All Docker containers are running
- ✅ Health endpoint returns 200 OK
- ✅ Models endpoint shows `"health": true`
- ✅ SSL certificate is valid (lock icon in browser)
- ✅ Swagger UI is accessible
- ✅ No errors in logs
- ✅ Backups are running
- ✅ Monitoring is active

---

## 🎉 Congratulations!

Once all items are checked, your AgentsFlowAI backend is live!

**Your API is now available at:**
- https://api.yourdomain.com

**Next steps:**
1. Deploy frontend
2. Update frontend API URL
3. Test complete application
4. Monitor and optimize

---

**Total Time**: ~2-3 hours  
**Difficulty**: Easy ⭐  
**Cost**: $20/month

**You did it! 🚀**
