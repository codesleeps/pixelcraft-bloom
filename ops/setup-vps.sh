#!/bin/bash
set -euo pipefail

# PixelCraft Bloom VPS Setup Script
# Usage: ./setup-vps.sh [domain] [email]
# Example: ./setup-vps.sh api.yourdomain.com admin@yourdomain.com

DOMAIN=${1:-""}
EMAIL=${2:-""}
APP_USER="pixelcraft"
APP_DIR="/opt/pixelcraft-bloom"
LOG_DIR="/var/log/pixelcraft"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

validate_inputs() {
    if [[ -z "$DOMAIN" ]]; then
        error "Domain is required. Usage: $0 <domain> <email>"
    fi
    if [[ -z "$EMAIL" ]]; then
        error "Email is required. Usage: $0 <domain> <email>"
    fi
}

update_system() {
    log "Updating system packages..."
    apt update && apt upgrade -y
    apt install -y curl wget git unzip software-properties-common
}

install_python() {
    log "Installing Python 3.11..."
    add-apt-repository ppa:deadsnakes/ppa -y
    apt update
    apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
    
    # Set Python 3.11 as default
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
    update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3 1
}

install_nginx() {
    log "Installing Nginx..."
    apt install -y nginx
    systemctl enable nginx
    systemctl start nginx
}

install_certbot() {
    log "Installing Certbot for SSL..."
    apt install -y certbot python3-certbot-nginx
}

install_redis() {
    log "Installing Redis..."
    apt install -y redis-server
    systemctl enable redis-server
    systemctl start redis-server
    
    # Configure Redis for production
    sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
    sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    systemctl restart redis-server
}

create_app_user() {
    log "Creating application user..."
    if ! id "$APP_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir "$APP_DIR" --create-home "$APP_USER"
    fi
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    chown "$APP_USER:$APP_USER" "$LOG_DIR"
}

setup_firewall() {
    log "Configuring UFW firewall..."
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw reload
}

clone_repository() {
    log "Setting up application directory..."
    if [[ ! -d "$APP_DIR" ]]; then
        mkdir -p "$APP_DIR"
    fi
    
    # Note: In production, you'd clone from your actual repo
    # git clone https://github.com/yourusername/pixelcraft-bloom.git "$APP_DIR"
    # For now, we'll create the structure
    mkdir -p "$APP_DIR/backend"
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
}

setup_python_env() {
    log "Setting up Python virtual environment..."
    sudo -u "$APP_USER" python3.11 -m venv "$APP_DIR/backend/.venv"
    
    # Install gunicorn and uvicorn for production
    sudo -u "$APP_USER" "$APP_DIR/backend/.venv/bin/pip" install --upgrade pip
    sudo -u "$APP_USER" "$APP_DIR/backend/.venv/bin/pip" install gunicorn uvicorn[standard]
    
    # Note: In production, you'd install from requirements.txt
    # sudo -u "$APP_USER" "$APP_DIR/backend/.venv/bin/pip" install -r "$APP_DIR/backend/requirements.txt"
}

configure_nginx() {
    log "Configuring Nginx..."
    
    # Copy our nginx config (assuming it exists in the repo)
    if [[ -f "$APP_DIR/ops/nginx.conf" ]]; then
        cp "$APP_DIR/ops/nginx.conf" "/etc/nginx/sites-available/pixelcraft-api"
    else
        # Create basic config if not found
        cat > "/etc/nginx/sites-available/pixelcraft-api" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    fi
    
    # Replace placeholder domain
    sed -i "s/api\.yourdomain\.com/$DOMAIN/g" "/etc/nginx/sites-available/pixelcraft-api"
    
    # Enable site
    ln -sf "/etc/nginx/sites-available/pixelcraft-api" "/etc/nginx/sites-enabled/"
    rm -f "/etc/nginx/sites-enabled/default"
    
    # Test configuration
    nginx -t
    systemctl reload nginx
}

setup_systemd() {
    log "Setting up systemd service..."
    
    if [[ -f "$APP_DIR/ops/pixelcraft-api.service" ]]; then
        cp "$APP_DIR/ops/pixelcraft-api.service" "/etc/systemd/system/"
    else
        error "Systemd service file not found at $APP_DIR/ops/pixelcraft-api.service"
    fi
    
    systemctl daemon-reload
    systemctl enable pixelcraft-api
}

setup_ssl() {
    log "Setting up SSL certificate..."
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect
}

create_env_template() {
    log "Creating environment template..."
    cat > "$APP_DIR/backend/.env.example" << EOF
# Production Environment Configuration
# Copy to .env and fill in actual values

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DB_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
BACKUP_ENCRYPTION_KEY=your-backup-encryption-passphrase

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-here
ADMIN_JWT_TOKEN=your-admin-token-here
USER_JWT_TOKEN=your-user-token-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
ENVIRONMENT=production

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/pixelcraft/app.log

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# External Services (if needed)
OPENAI_API_KEY=your-openai-key-if-needed
ANTHROPIC_API_KEY=your-anthropic-key-if-needed
EOF
    
    chown "$APP_USER:$APP_USER" "$APP_DIR/backend/.env.example"
    
    warn "Don't forget to copy .env.example to .env and fill in actual values!"
}

print_next_steps() {
    log "Setup complete! Next steps:"
    echo ""
    echo "1. Copy your application code to $APP_DIR"
    echo "2. Copy $APP_DIR/backend/.env.example to $APP_DIR/backend/.env"
    echo "3. Fill in actual values in $APP_DIR/backend/.env"
    echo "4. Install Python dependencies:"
    echo "   sudo -u $APP_USER $APP_DIR/backend/.venv/bin/pip install -r $APP_DIR/backend/requirements.txt"
    echo "5. Start the service:"
    echo "   systemctl start pixelcraft-api"
    echo "6. Check service status:"
    echo "   systemctl status pixelcraft-api"
    echo "7. View logs:"
    echo "   journalctl -u pixelcraft-api -f"
    echo ""
    echo "Your API will be available at: https://$DOMAIN"
    echo "Health check: https://$DOMAIN/health"
}

main() {
    log "Starting PixelCraft Bloom VPS setup..."
    
    check_root
    validate_inputs
    
    update_system
    install_python
    install_nginx
    install_certbot
    install_redis
    create_app_user
    setup_firewall
    clone_repository
    setup_python_env
    configure_nginx
    setup_systemd
    setup_ssl
    create_env_template
    
    print_next_steps
    
    log "VPS setup completed successfully!"
}

# Run main function
main "$@"