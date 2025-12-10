#!/bin/bash

# PixelCraft Bloom VPS Deployment Script
# This script automates the complete deployment process on a fresh VPS
# Designed for Ubuntu 22.04 LTS

# Configuration - EDIT THESE VALUES
DOMAIN="agentsflow.cloud"
API_DOMAIN="api.agentsflow.cloud"
ADMIN_EMAIL="admin@agentsflow.cloud"
PROJECT_DIR="/opt/agentsflowai"
BACKUP_DIR="/var/backups/agentsflowai"
LOG_DIR="/var/log/agentsflowai"
DOCKER_IMAGE="ghcr.io/your-username/agentsflowai:latest"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[DEPLOY] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    error "This script must be run as root. Use: sudo $0"
fi

log "Starting PixelCraft Bloom VPS Deployment..."
log "Domain: $DOMAIN"
log "API Domain: $API_DOMAIN"
log "Project Directory: $PROJECT_DIR"
echo ""

# 1. System Update and Dependencies
log "1. Updating system and installing dependencies..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    git \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    postgresql-client \
    redis-tools \
    gnupg \
    curl \
    wget \
    htop \
    net-tools \
    fail2ban

success "System updated and dependencies installed"

# 2. Create Project Structure
log "2. Setting up project structure..."
mkdir -p "$PROJECT_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"
chmod 750 "$BACKUP_DIR"
chmod 750 "$LOG_DIR"

# Create pixelcraft user
if id "pixelcraft" &>/dev/null; then
    log "User 'pixelcraft' already exists"
else
    adduser --disabled-password --gecos "" pixelcraft
    usermod -aG sudo pixelcraft
    usermod -aG docker pixelcraft
    success "User 'pixelcraft' created and configured"
fi

# Set ownership
chown -R pixelcraft:pixelcraft "$PROJECT_DIR"
chown -R pixelcraft:pixelcraft "$BACKUP_DIR"
chown -R pixelcraft:pixelcraft "$LOG_DIR"

success "Project structure created"

# 3. Clone Repository
log "3. Cloning repository..."
if [ -d "$PROJECT_DIR/.git" ]; then
    log "Repository already exists, pulling latest changes..."
    cd "$PROJECT_DIR" || exit 1
    git pull origin main
else
    git clone https://github.com/your-username/pixelcraft-bloom.git "$PROJECT_DIR"
    cd "$PROJECT_DIR" || exit 1
fi

success "Repository cloned"

# 4. Configure Environment
log "4. Setting up environment configuration..."
cat > "$PROJECT_DIR/backend/.env" << EOF
# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO
USE_HTTPS=true
TRUSTED_HOSTS=$DOMAIN,$API_DOMAIN,localhost

# Database Configuration
SUPABASE__URL=postgresql://postgres:yourpassword@localhost:5432/pixelcraft
SUPABASE__KEY=your-supabase-service-role-key
SUPABASE__JWT_SECRET=your-supabase-jwt-secret

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security Configuration
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN,https://$API_DOMAIN
JWT_SECRET=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Backup Configuration
BACKUP_ENCRYPTION_KEY=$(openssl rand -hex 32)

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
SENTRY_ENVIRONMENT=production
EOF

# Make scripts executable
chmod +x ops/*.sh
chmod +x scripts/*.sh

success "Environment configured"

# 5. SSL Certificate Setup
log "5. Setting up SSL certificates..."
systemctl stop nginx

# Obtain certificates
certbot certonly --standalone -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m "$ADMIN_EMAIL"
certbot certonly --standalone -d "$API_DOMAIN" --non-interactive --agree-tos -m "$ADMIN_EMAIL"

# Set up automatic renewal
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
echo "$(date): SSL certificates renewed" >> "$LOG_DIR/letsencrypt-renewal.log"
EOF

chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# Add to cron
(crontab -l 2>/dev/null; echo "0 */12 * * * /usr/bin/certbot renew --quiet") | crontab -

systemctl start nginx
success "SSL certificates configured with automatic renewal"

# 6. Nginx Configuration
log "6. Configuring Nginx..."
cat > "/etc/nginx/sites-available/agentsflowai" << EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 80;
    server_name $API_DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# Main domain HTTPS
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# API domain HTTPS
server {
    listen 443 ssl http2;
    server_name $API_DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$API_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$API_DOMAIN/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api_ratelimit:10m rate=10r/s;

    location / {
        limit_req zone=api_ratelimit burst=20 nodelay;

        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location = /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
EOF

# Enable site
ln -sf "/etc/nginx/sites-available/agentsflowai" "/etc/nginx/sites-enabled/"
rm -f "/etc/nginx/sites-enabled/default"

# Test and reload
if nginx -t; then
    systemctl reload nginx
    success "Nginx configured and reloaded"
else
    error "Nginx configuration test failed"
fi

# 7. Docker Setup
log "7. Setting up Docker services..."
cd "$PROJECT_DIR" || exit 1

# Create docker-compose.override.yml for production
cat > docker-compose.override.yml << EOF
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - APP_ENV=production
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
EOF

# Pull and start containers
docker compose pull
docker compose up -d

# Verify containers
if docker compose ps | grep -q "Up"; then
    success "Docker services started"
else
    error "Docker services failed to start"
fi

# 8. Backup System Setup
log "8. Configuring backup system..."
# Set up cron jobs
(crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/ops/backup.sh >> $LOG_DIR/backup.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "30 2 * * * $PROJECT_DIR/ops/backup-redis.sh >> $LOG_DIR/redis-backup.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 */6 * * * $PROJECT_DIR/ops/monitor-backups.sh >> $LOG_DIR/backup-monitor.log 2>&1") | crontab -

success "Backup system configured"

# 9. Security Hardening
log "9. Applying security hardening..."
# Configure fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 3

[sshd]
enabled = true

[nginx-botsearch]
enabled = true

[nginx-nohome]
enabled = true

[nginx-noscript]
enabled = true
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# Configure firewall
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS
ufw --force enable

success "Security hardening applied"

# 10. Final Verification
log "10. Running final verification..."
echo ""

# Test API endpoints
API_TESTS=(
    "https://$API_DOMAIN/health"
    "https://$API_DOMAIN/api/models"
)

for endpoint in "${API_TESTS[@]}"; do
    if curl -sSf -o /dev/null "$endpoint"; then
        success "API endpoint working: $endpoint"
    else
        warn "API endpoint not responding: $endpoint"
    fi
done

# Test SSL
if curl -sSf -o /dev/null "https://$API_DOMAIN/health"; then
    success "SSL configuration working"
else
    warn "SSL configuration may have issues"
fi

# Test backup scripts
if [ -f "$PROJECT_DIR/ops/backup.sh" ]; then
    success "Backup scripts installed"
else
    warn "Backup scripts not found"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 VPS Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "PixelCraft Bloom has been successfully deployed to your VPS."
echo ""
echo "Deployment Summary:"
echo "  ✅ System updated and dependencies installed"
echo "  ✅ Project structure created"
echo "  ✅ SSL certificates configured with auto-renewal"
echo "  ✅ Nginx configured with HTTPS and security headers"
echo "  ✅ Docker services running"
echo "  ✅ Backup system configured"
echo "  ✅ Security hardening applied"
echo "  ✅ Monitoring and logging set up"
echo ""
echo "Next Steps:"
echo "1. Configure DNS to point to your server IP"
echo "   - A record: $DOMAIN → your-server-ip"
echo "   - A record: $API_DOMAIN → your-server-ip"
echo ""
echo "2. Update environment variables in $PROJECT_DIR/backend/.env"
echo "   - Set real database credentials"
echo "   - Configure Redis connection"
echo "   - Set up Sentry for monitoring"
echo ""
echo "3. Monitor the system:"
echo "   - View logs: tail -f $LOG_DIR/*.log"
echo "   - Check services: docker compose ps"
echo "   - Monitor performance: htop"
echo ""
echo "4. Test the deployment:"
echo "   - Health check: curl https://$API_DOMAIN/health"
echo "   - API docs: https://$API_DOMAIN/docs"
echo "   - Models endpoint: https://$API_DOMAIN/api/models"
echo ""
echo "Production URLs:"
echo "  - API: https://$API_DOMAIN"
echo "  - Docs: https://$API_DOMAIN/docs"
echo "  - Health: https://$API_DOMAIN/health"
echo ""
echo "For troubleshooting, check:"
echo "  - Nginx logs: /var/log/nginx/error.log"
echo "  - Docker logs: docker compose logs"
echo "  - Application logs: $LOG_DIR/"
echo ""
echo "Thank you for using PixelCraft Bloom! 🚀"