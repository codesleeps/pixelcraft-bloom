# SSL Certificate Setup for Custom Domain

This guide covers setting up SSL certificates for PixelCraft Bloom using Let's Encrypt with certbot, configuring nginx as a reverse proxy, and enabling automatic certificate renewal.

## Prerequisites

- Ubuntu/Debian server with root or sudo access
- Custom domain (e.g., `pixelcraft-bloom.com`)
- DNS configured to point to your server IP
- Nginx installed and configured
- Firewall allowing ports 80 and 443

## 1. Domain Setup

### DNS Configuration

Point your domain to the server IP:

```bash
# Example DNS records (replace with your actual IP)
# A record: pixelcraft-bloom.com -> YOUR_SERVER_IP
# A record: api.pixelcraft-bloom.com -> YOUR_SERVER_IP
# A record: www.pixelcraft-bloom.com -> YOUR_SERVER_IP (optional)
```

Verify DNS propagation:
```bash
nslookup pixelcraft-bloom.com
nslookup api.pixelcraft-bloom.com
```

## 2. Install Certbot

```bash
# Update package list
sudo apt update

# Install certbot and nginx plugin
sudo apt install certbot python3-certbot-nginx

# Verify installation
certbot --version
```

## 3. Obtain SSL Certificates

### Option A: Automatic nginx integration (Recommended)

```bash
# Stop nginx temporarily (certbot will restart it)
sudo systemctl stop nginx

# Obtain certificate for main domain
sudo certbot certonly --standalone -d pixelcraft-bloom.com -d www.pixelcraft-bloom.com

# Obtain certificate for API subdomain
sudo certbot certonly --standalone -d api.pixelcraft-bloom.com

# Start nginx again
sudo systemctl start nginx
```

### Option B: Manual nginx configuration

If you prefer to configure nginx manually:

```bash
# Obtain certificates without nginx integration
sudo certbot certonly --standalone -d pixelcraft-bloom.com -d www.pixelcraft-bloom.com
sudo certbot certonly --standalone -d api.pixelcraft-bloom.com
```

## 4. Configure Nginx for HTTPS

Update your nginx configuration to support SSL:

```nginx
# /etc/nginx/sites-available/pixelcraft-bloom
server {
    listen 80;
    server_name pixelcraft-bloom.com www.pixelcraft-bloom.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name pixelcraft-bloom.com www.pixelcraft-bloom.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/pixelcraft-bloom.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pixelcraft-bloom.com/privkey.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Frontend static files
    root /var/www/pixelcraft-bloom;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}

# API Subdomain
server {
    listen 80;
    server_name api.pixelcraft-bloom.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.pixelcraft-bloom.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.pixelcraft-bloom.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.pixelcraft-bloom.com/privkey.pem;

    # SSL Security Settings (same as above)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_ratelimit:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    location / {
        limit_req zone=api_ratelimit burst=20 nodelay;
        limit_conn addr 10;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # CORS preflight
    if ($request_method = OPTIONS) {
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With";
        add_header Access-Control-Max-Age 86400;
        return 204;
    }
}
```

Enable the site:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/pixelcraft-bloom /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## 5. Configure FastAPI for HTTPS

Update your FastAPI configuration to handle HTTPS properly:

```python
# backend/app/config.py
class Settings(BaseSettings):
    # ... existing settings ...

    # HTTPS/SSL settings
    use_https: bool = Field(default=True, env="USE_HTTPS")
    trusted_hosts: List[str] = Field(default=["pixelcraft-bloom.com", "api.pixelcraft-bloom.com"], env="TRUSTED_HOSTS")

    # CORS settings for HTTPS
    cors_origins: List[str] = Field(
        default=[
            "https://pixelcraft-bloom.com",
            "https://www.pixelcraft-bloom.com",
            "https://api.pixelcraft-bloom.com"
        ],
        env="CORS_ORIGINS"
    )
```

Update main.py to use HTTPS settings:

```python
# backend/app/main.py
def create_app() -> FastAPI:
    # ... existing code ...

    # CORS with HTTPS origins
    origins = settings.cors_origins if settings.use_https else settings.parsed_cors()
    if not origins:
        origins = ["http://localhost:5173", "http://localhost:8080"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted hosts middleware for security
    if settings.use_https:
        from starlette.middleware.trustedhost import TrustedHostMiddleware
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    # ... rest of the code ...
```

## 6. Automatic Certificate Renewal

### Setup Cron Job

```bash
# Edit crontab
sudo crontab -e

# Add this line to run certbot renewal twice daily
0 */12 * * * /usr/bin/certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

### Test Renewal

```bash
# Test renewal process
sudo certbot renew --dry-run

# Check renewal status
sudo certbot certificates
```

### Renewal Hook Script

Create a renewal hook script:

```bash
#!/bin/bash
# /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# Reload nginx after certificate renewal
systemctl reload nginx

# Log the renewal
echo "$(date): SSL certificates renewed and nginx reloaded" >> /var/log/letsencrypt-renewal.log

# Optional: Send notification
# curl -X POST -H 'Content-type: application/json' \
#   --data '{"text":"SSL certificates renewed for pixelcraft-bloom.com"}' \
#   YOUR_SLACK_WEBHOOK_URL
```

Make it executable:
```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

## 7. Monitoring & Alerts

### SSL Certificate Expiry Monitoring

```bash
#!/bin/bash
# /opt/pixelcraft/scripts/check-ssl-expiry.sh

WARNING_DAYS=30
CRITICAL_DAYS=7

# Check certificate expiry
EXPIRY_DATE=$(openssl s_client -connect pixelcraft-bloom.com:443 -servername pixelcraft-bloom.com 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d'=' -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

if [ $DAYS_LEFT -le $CRITICAL_DAYS ]; then
    echo "CRITICAL: SSL certificate expires in $DAYS_LEFT days"
    # Send critical alert
    exit 2
elif [ $DAYS_LEFT -le $WARNING_DAYS ]; then
    echo "WARNING: SSL certificate expires in $DAYS_LEFT days"
    # Send warning alert
    exit 1
else
    echo "OK: SSL certificate expires in $DAYS_LEFT days"
    exit 0
fi
```

Add to cron for daily checks:
```bash
# /etc/cron.d/ssl-monitoring
0 9 * * * root /opt/pixelcraft/scripts/check-ssl-expiry.sh
```

## 8. Troubleshooting

### Common Issues

#### Certificate Not Renewing
```bash
# Check certbot logs
sudo journalctl -u certbot

# Manual renewal
sudo certbot renew --force-renewal
```

#### Mixed Content Warnings
- Ensure all internal links use HTTPS
- Update API_BASE_URL in frontend config
- Check for hardcoded HTTP URLs in code

#### SSL Handshake Failures
```bash
# Test SSL connection
openssl s_client -connect pixelcraft-bloom.com:443 -servername pixelcraft-bloom.com

# Check certificate chain
openssl s_client -connect pixelcraft-bloom.com:443 -servername pixelcraft-bloom.com | openssl x509 -text
```

#### Nginx SSL Errors
```bash
# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t
sudo systemctl reload nginx
```

## 9. Security Best Practices

### SSL/TLS Configuration
- Use only TLS 1.2 and 1.3
- Disable weak ciphers
- Enable HSTS header
- Use secure session resumption

### Certificate Management
- Store certificates with restricted permissions
- Regularly rotate certificates
- Monitor certificate expiry
- Use certificate pinning if required

### Additional Security Headers
```nginx
# In nginx server block
add_header X-Content-Type-Options nosniff always;
add_header X-Frame-Options SAMEORIGIN always;
add_header Referrer-Policy strict-origin-when-cross-origin always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

## 10. Deployment Checklist

- [ ] Domain DNS configured and propagated
- [ ] Certbot installed and configured
- [ ] SSL certificates obtained for all domains
- [ ] Nginx configured for HTTPS
- [ ] FastAPI updated for HTTPS settings
- [ ] Automatic renewal configured
- [ ] SSL monitoring alerts set up
- [ ] Security headers implemented
- [ ] Mixed content issues resolved
- [ ] SSL test passed (ssltest.com or similar)

---

*Last updated: $(date)*
*SSL Setup Version: 1.0*
