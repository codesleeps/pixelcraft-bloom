# Hostinger VPS Deployment Guide - AgentsFlowAI Backend

**Complete Step-by-Step Guide**  
**Estimated Time**: 1-2 hours  
**Difficulty**: Easy ⭐

---

## 📋 Prerequisites

Before starting, have these ready:
- [ ] Domain name (e.g., agentsflowai.com)
- [ ] GitHub account with your code
- [ ] Supabase project URL and keys
- [ ] Credit card for Hostinger payment

---

## Part 1: Purchase & Setup Hostinger VPS

### Step 1: Sign Up for Hostinger VPS

1. **Go to Hostinger**
   - Visit: https://www.hostinger.com/vps-hosting
   
2. **Choose VPS Plan**
   - Select **VPS 4** plan
   - Specs: 4 vCPUs, 16GB RAM, 200GB SSD
   - Choose **12 months** for best price (~$20/month)

3. **Select Operating System**
   - Choose **Ubuntu 22.04 LTS** (64-bit)
   - This is the most stable and supported version

4. **Choose Data Center Location**
   - Select closest to your target users:
     - **USA**: East Coast (New York) or West Coast (Los Angeles)
     - **Europe**: Netherlands or UK
     - **Asia**: Singapore

5. **Complete Purchase**
   - Enter payment details
   - Complete checkout
   - Wait for VPS provisioning (5-10 minutes)

### Step 2: Access Your VPS

1. **Get VPS Credentials**
   - Check your email for VPS details
   - You'll receive:
     - IP address (e.g., 123.45.67.89)
     - Root password
     - SSH port (usually 22)

2. **Save Credentials Securely**
   ```
   VPS IP: ___________________
   Root Password: ___________________
   SSH Port: 22
   ```

---

## Part 2: Initial Server Setup

### Step 1: Connect to Your VPS

```bash
# From your local terminal
ssh root@YOUR_VPS_IP

# Enter the root password when prompted
# Type 'yes' when asked about fingerprint
```

**Expected output:**
```
Welcome to Ubuntu 22.04.3 LTS
root@vps-123456:~#
```

### Step 2: Update System

```bash
# Update package lists
apt update

# Upgrade all packages
apt upgrade -y

# This may take 5-10 minutes
```

### Step 3: Create Non-Root User (Security Best Practice)

```bash
# Create new user
adduser agentsflowai

# Enter password when prompted (save this!)
# Press Enter for other prompts (can leave blank)

# Add user to sudo group
usermod -aG sudo agentsflowai

# Switch to new user
su - agentsflowai
```

### Step 4: Set Up SSH Key Authentication (Optional but Recommended)

**On your local machine:**
```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub
# Copy the output
```

**Back on VPS (as agentsflowai user):**
```bash
# Create .ssh directory
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key
nano ~/.ssh/authorized_keys
# Paste your public key, save (Ctrl+X, Y, Enter)

# Set permissions
chmod 600 ~/.ssh/authorized_keys
```

**Test SSH key login:**
```bash
# From local machine (new terminal)
ssh agentsflowai@YOUR_VPS_IP

# Should login without password!
```

---

## Part 3: Install Required Software

### Step 1: Install Docker

```bash
# Install Docker using official script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Verify Docker installation
docker --version
# Should show: Docker version 24.x.x
```

### Step 2: Install Docker Compose

```bash
# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Verify installation
docker compose version
# Should show: Docker Compose version v2.x.x
```

### Step 3: Install Git

```bash
# Install Git
sudo apt install git -y

# Verify installation
git --version
# Should show: git version 2.x.x
```

### Step 4: Install Nginx (Web Server)

```bash
# Install Nginx
sudo apt install nginx -y

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
# Should show: active (running)
```

### Step 5: Install Certbot (SSL Certificates)

```bash
# Install Certbot for Let's Encrypt SSL
sudo apt install certbot python3-certbot-nginx -y

# Verify installation
certbot --version
# Should show: certbot 1.x.x
```

---

## Part 4: Configure Firewall

### Step 1: Set Up UFW Firewall

```bash
# Install UFW if not installed
sudo apt install ufw -y

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow backend port (optional, if direct access needed)
sudo ufw allow 8000/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
8000/tcp                   ALLOW       Anywhere
```

---

## Part 5: Deploy AgentsFlowAI Backend

### Step 1: Clone Your Repository

```bash
# Navigate to home directory
cd ~

# Clone your repository
git clone https://github.com/YOUR_USERNAME/agentsflowai.git

# Navigate to project
cd agentsflowai

# Verify files
ls -la
# Should see: backend/, frontend/, docker-compose.yml, etc.
```

### Step 2: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Update these values in .env:**
```bash
# Application
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Supabase (with double underscores!)
SUPABASE__URL=https://your-project.supabase.co
SUPABASE__KEY=your-service-role-key-here
SUPABASE__JWT_SECRET=your-jwt-secret-here

# Redis (Docker service name)
REDIS_URL=redis://redis:6379/0

# Ollama (Docker service name)
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=mistral:7b

# Database (if using local PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres

# Optional: Sentry for error tracking
SENTRY_DSN=your-sentry-dsn-here
SENTRY_ENVIRONMENT=production
```

**Save and exit**: Ctrl+X, Y, Enter

### Step 3: Start Docker Services

```bash
# Pull latest images
docker compose pull

# Start services in detached mode
docker compose up -d

# This will take 5-10 minutes on first run
```

**Monitor startup:**
```bash
# Watch logs
docker compose logs -f backend

# Wait for this message:
# "INFO:     Application startup complete."
# "INFO:     ModelManager initialized"

# Press Ctrl+C to exit logs
```

### Step 4: Verify Services Are Running

```bash
# Check running containers
docker compose ps

# Should show:
# backend    running
# redis      running
# ollama     running
# db         running (if using local PostgreSQL)
```

### Step 5: Pull Ollama Models

```bash
# Pull mistral model (this takes 10-15 minutes)
docker compose exec ollama ollama pull mistral:7b

# Optional: Pull mixtral model (takes 20-30 minutes)
docker compose exec ollama ollama pull mixtral:8x7b

# Verify models are available
docker compose exec ollama ollama list
```

### Step 6: Test Backend Locally

```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return JSON with status

# Test model endpoints
curl http://localhost:8000/api/models

# Should return list of models with health: true
```

---

## Part 6: Configure Domain & SSL

### Step 1: Point Domain to VPS

**In your domain registrar (e.g., Namecheap, GoDaddy):**

1. **Add A Records:**
   ```
   Type: A
   Host: @
   Value: YOUR_VPS_IP
   TTL: 300

   Type: A
   Host: api
   Value: YOUR_VPS_IP
   TTL: 300
   ```

2. **Wait for DNS propagation** (5-30 minutes)
   ```bash
   # Check DNS propagation
   nslookup yourdomain.com
   nslookup api.yourdomain.com
   
   # Should return your VPS IP
   ```

### Step 2: Configure Nginx

```bash
# Create Nginx configuration for backend
sudo nano /etc/nginx/sites-available/agentsflowai-backend
```

**Add this configuration:**
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # Increase timeouts for AI processing
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    # Increase buffer sizes
    client_max_body_size 50M;
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support
    location /api/ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

**Save and exit**: Ctrl+X, Y, Enter

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/agentsflowai-backend /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Should show: syntax is ok

# Reload Nginx
sudo systemctl reload nginx
```

### Step 3: Install SSL Certificate

```bash
# Get SSL certificate from Let's Encrypt
sudo certbot --nginx -d api.yourdomain.com

# Follow prompts:
# - Enter email address
# - Agree to terms (Y)
# - Share email (optional)
# - Redirect HTTP to HTTPS (choose 2)

# Certificate will auto-renew every 90 days
```

### Step 4: Test SSL

```bash
# Test HTTPS endpoint
curl https://api.yourdomain.com/health

# Should return JSON with status

# Test in browser
# Visit: https://api.yourdomain.com/docs
# Should show Swagger UI with SSL lock icon
```

---

## Part 7: Set Up Automatic Backups

### Step 1: Create Backup Script

```bash
# Create backup directory
mkdir -p ~/backups

# Create backup script
nano ~/backup.sh
```

**Add this script:**
```bash
#!/bin/bash
# AgentsFlowAI Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups
PROJECT_DIR=~/agentsflowai

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Docker volumes
docker run --rm \
  -v agentsflowai_db_data:/data \
  -v $BACKUP_DIR:/backup \
  ubuntu tar czf /backup/db_backup_$DATE.tar.gz /data

docker run --rm \
  -v agentsflowai_ollama_data:/data \
  -v $BACKUP_DIR:/backup \
  ubuntu tar czf /backup/ollama_backup_$DATE.tar.gz /data

# Backup environment files
cp $PROJECT_DIR/.env $BACKUP_DIR/env_backup_$DATE

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "env_backup_*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Save and exit**: Ctrl+X, Y, Enter

```bash
# Make script executable
chmod +x ~/backup.sh

# Test backup
~/backup.sh

# Check backups
ls -lh ~/backups/
```

### Step 2: Schedule Automatic Backups

```bash
# Edit crontab
crontab -e

# Choose editor (nano is easiest)
# Add this line at the end:
0 2 * * * /home/agentsflowai/backup.sh >> /home/agentsflowai/backup.log 2>&1

# This runs backup daily at 2 AM
```

**Save and exit**: Ctrl+X, Y, Enter

---

## Part 8: Set Up Monitoring

### Step 1: Install Monitoring Tools

```bash
# Install htop for system monitoring
sudo apt install htop -y

# Install netdata for web-based monitoring (optional)
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Access netdata at: http://YOUR_VPS_IP:19999
```

### Step 2: Set Up Log Rotation

```bash
# Create log rotation config
sudo nano /etc/logrotate.d/agentsflowai
```

**Add this configuration:**
```
/home/agentsflowai/agentsflowai/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 agentsflowai agentsflowai
}
```

**Save and exit**: Ctrl+X, Y, Enter

### Step 3: Monitor Docker Logs

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend

# View last 100 lines
docker compose logs --tail=100 backend

# Save logs to file
docker compose logs > ~/docker-logs-$(date +%Y%m%d).log
```

---

## Part 9: Performance Optimization

### Step 1: Enable Docker Logging Limits

```bash
# Edit docker daemon config
sudo nano /etc/docker/daemon.json
```

**Add this configuration:**
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

**Save and exit**, then restart Docker:
```bash
sudo systemctl restart docker
docker compose up -d
```

### Step 2: Optimize Nginx

```bash
# Edit Nginx config
sudo nano /etc/nginx/nginx.conf
```

**Update these values in http block:**
```nginx
http {
    # ... existing config ...
    
    # Optimize performance
    worker_processes auto;
    worker_connections 1024;
    keepalive_timeout 65;
    
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;
    
    # ... rest of config ...
}
```

**Save and exit**, then reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Part 10: Final Verification

### Step 1: Run Complete Health Check

```bash
# Test all endpoints
curl https://api.yourdomain.com/health
curl https://api.yourdomain.com/api/models
curl https://api.yourdomain.com/api/models/mistral

# All should return 200 OK with JSON
```

### Step 2: Test from External Location

**From your local machine:**
```bash
# Test health
curl https://api.yourdomain.com/health | jq .

# Test models
curl https://api.yourdomain.com/api/models | jq .

# Test Swagger UI
# Open in browser: https://api.yourdomain.com/docs
```

### Step 3: Load Test (Optional)

```bash
# Install Apache Bench
sudo apt install apache2-utils -y

# Run simple load test
ab -n 100 -c 10 https://api.yourdomain.com/health

# Should handle 100 requests with 10 concurrent
```

---

## 🎯 Deployment Checklist

### Pre-Deployment
- [ ] Hostinger VPS purchased and provisioned
- [ ] Domain name configured
- [ ] Supabase project ready
- [ ] GitHub repository accessible

### Server Setup
- [ ] SSH access working
- [ ] Non-root user created
- [ ] Docker installed and running
- [ ] Nginx installed and configured
- [ ] Firewall configured (UFW)

### Application Deployment
- [ ] Code cloned from GitHub
- [ ] Environment variables configured
- [ ] Docker containers running
- [ ] Ollama models pulled
- [ ] Backend responding on localhost:8000

### Domain & SSL
- [ ] DNS A records configured
- [ ] DNS propagated (nslookup works)
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate installed
- [ ] HTTPS working

### Monitoring & Backups
- [ ] Backup script created
- [ ] Cron job scheduled
- [ ] Log rotation configured
- [ ] Monitoring tools installed

### Final Testing
- [ ] Health endpoint working
- [ ] Model endpoints working
- [ ] Swagger UI accessible
- [ ] WebSocket connections working
- [ ] SSL certificate valid

---

## 🚀 Post-Deployment

### Daily Tasks
```bash
# Check service status
docker compose ps

# Check logs for errors
docker compose logs --tail=50 backend | grep ERROR

# Check disk space
df -h

# Check memory usage
free -h
```

### Weekly Tasks
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Check backup logs
tail -50 ~/backup.log

# Review Docker logs
docker compose logs --since 7d > weekly-logs.txt
```

### Monthly Tasks
```bash
# Review SSL certificate expiry
sudo certbot certificates

# Clean up Docker
docker system prune -a

# Review and optimize database
# (if using local PostgreSQL)
```

---

## 🆘 Troubleshooting

### Issue: Can't SSH into VPS

**Solution:**
```bash
# Check if SSH service is running
sudo systemctl status ssh

# Restart SSH service
sudo systemctl restart ssh

# Check firewall
sudo ufw status

# Ensure port 22 is allowed
sudo ufw allow 22/tcp
```

### Issue: Docker containers won't start

**Solution:**
```bash
# Check Docker service
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Check logs
docker compose logs

# Rebuild containers
docker compose down
docker compose up -d --build
```

### Issue: Nginx shows 502 Bad Gateway

**Solution:**
```bash
# Check if backend is running
docker compose ps backend

# Check backend logs
docker compose logs backend

# Test backend directly
curl http://localhost:8000/health

# Restart Nginx
sudo systemctl restart nginx
```

### Issue: SSL certificate fails

**Solution:**
```bash
# Check DNS is propagated
nslookup api.yourdomain.com

# Check Nginx config
sudo nginx -t

# Try manual certificate
sudo certbot certonly --standalone -d api.yourdomain.com

# Check firewall
sudo ufw status
# Ensure ports 80 and 443 are open
```

### Issue: Out of disk space

**Solution:**
```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a -f

# Remove old logs
sudo journalctl --vacuum-time=7d

# Remove old backups
find ~/backups -mtime +7 -delete
```

### Issue: High memory usage

**Solution:**
```bash
# Check memory
free -h

# Check Docker stats
docker stats

# Restart Ollama (memory intensive)
docker compose restart ollama

# Consider upgrading to VPS 8 (32GB RAM)
```

---

## 📞 Support Resources

### Hostinger Support
- **Live Chat**: 24/7 available in Hostinger panel
- **Knowledge Base**: https://support.hostinger.com
- **Email**: support@hostinger.com

### AgentsFlowAI Documentation
- **Production Guide**: ops/PRODUCTION_READINESS_COMPLETE.md
- **Quick Reference**: DEPLOYMENT_QUICK_REFERENCE.md
- **Troubleshooting**: Backend logs and health endpoints

### Community Resources
- **Docker Docs**: https://docs.docker.com
- **Nginx Docs**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/docs/

---

## 🎉 Success!

Your AgentsFlowAI backend is now deployed on Hostinger VPS!

**Your endpoints:**
- **API**: https://api.yourdomain.com
- **Health**: https://api.yourdomain.com/health
- **Models**: https://api.yourdomain.com/api/models
- **Docs**: https://api.yourdomain.com/docs

**Next steps:**
1. Deploy frontend to Vercel/Netlify
2. Update frontend to use your API URL
3. Test end-to-end functionality
4. Monitor performance and logs
5. Set up error tracking (Sentry)

---

**Congratulations on your deployment! 🚀**
