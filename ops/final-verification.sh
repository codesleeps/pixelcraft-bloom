#!/bin/bash

# AgentsFlowAI Final Deployment Verification Script
# This script verifies that all deployment components are working correctly

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Configuration
DOMAIN="agentsflow.cloud"
API_DOMAIN="api.agentsflow.cloud"
BACKUP_DIR="/var/backups/pixelcraft"
LOG_DIR="/var/log/pixelcraft"
PROJECT_DIR="/opt/agentsflowai"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script should be run as root for complete verification."
    echo "Some checks will be skipped."
    RUNNING_AS_ROOT=false
else
    RUNNING_AS_ROOT=true
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AgentsFlowAI Deployment Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. System Requirements Check
echo -e "${BLUE}1. System Requirements Check${NC}"
echo "----------------------------------------"

REQUIRED_COMMANDS=("docker" "docker-compose" "nginx" "certbot" "redis-cli" "pg_isready" "gpg")
MISSING_COMMANDS=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        log_success "$cmd is installed"
    else
        log_error "$cmd is NOT installed"
        MISSING_COMMANDS+=("$cmd")
    fi
done

if [ ${#MISSING_COMMANDS[@]} -eq 0 ]; then
    log_success "All required commands are installed"
else
    log_error "Missing commands: ${MISSING_COMMANDS[*]}"
fi
echo ""

# 2. Directory Structure Check
echo -e "${BLUE}2. Directory Structure Check${NC}"
echo "----------------------------------------"

if [ -d "$PROJECT_DIR" ]; then
    log_success "Project directory exists: $PROJECT_DIR"
else
    log_error "Project directory NOT found: $PROJECT_DIR"
fi

if [ -d "$BACKUP_DIR" ]; then
    log_success "Backup directory exists: $BACKUP_DIR"
else
    log_warning "Backup directory NOT found: $BACKUP_DIR"
fi

if [ -d "$LOG_DIR" ]; then
    log_success "Log directory exists: $LOG_DIR"
else
    log_warning "Log directory NOT found: $LOG_DIR"
fi
echo ""

# 3. SSL Certificate Check
echo -e "${BLUE}3. SSL Certificate Check${NC}"
echo "----------------------------------------"

if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    log_success "SSL certificate exists for $DOMAIN"

    # Check certificate expiry
    EXPIRY_DATE=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" 2>/dev/null | cut -d= -f2)
    if [ -n "$EXPIRY_DATE" ]; then
        EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || echo 0)
        CURRENT_EPOCH=$(date +%s)
        DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

        if [ "$DAYS_LEFT" -gt 30 ]; then
            log_success "Certificate expires in $DAYS_LEFT days (valid)"
        elif [ "$DAYS_LEFT" -gt 7 ]; then
            log_warning "Certificate expires in $DAYS_LEFT days (warning)"
        else
            log_error "Certificate expires in $DAYS_LEFT days (critical)"
        fi
    fi
else
    log_error "SSL certificate NOT found for $DOMAIN"
fi

if [ -f "/etc/letsencrypt/live/$API_DOMAIN/fullchain.pem" ]; then
    log_success "SSL certificate exists for $API_DOMAIN"
else
    log_error "SSL certificate NOT found for $API_DOMAIN"
fi
echo ""

# 4. Nginx Configuration Check
echo -e "${BLUE}4. Nginx Configuration Check${NC}"
echo "----------------------------------------"

if systemctl is-active --quiet nginx; then
    log_success "Nginx service is running"
else
    log_error "Nginx service is NOT running"
fi

if nginx -t 2>/dev/null; then
    log_success "Nginx configuration is valid"
else
    log_error "Nginx configuration has errors"
fi

if [ -f "/etc/nginx/sites-available/agentsflowai" ]; then
    log_success "Nginx site configuration exists"
else
    log_error "Nginx site configuration NOT found"
fi
echo ""

# 5. Docker Services Check
echo -e "${BLUE}5. Docker Services Check${NC}"
echo "----------------------------------------"

if systemctl is-active --quiet docker; then
    log_success "Docker service is running"
else
    log_error "Docker service is NOT running"
fi

if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    log_success "Docker Compose file exists"

    if $RUNNING_AS_ROOT; then
        cd "$PROJECT_DIR" || exit 1
        if docker compose ps 2>/dev/null | grep -q "Up"; then
            log_success "Docker containers are running"
        else
            log_error "Docker containers are NOT running"
        fi
    else
        log_warning "Skipping Docker container check (not running as root)"
    fi
else
    log_error "Docker Compose file NOT found"
fi
echo ""

# 6. Backup System Check
echo -e "${BLUE}6. Backup System Check${NC}"
echo "----------------------------------------"

BACKUP_SCRIPTS=(
    "$PROJECT_DIR/ops/backup.sh"
    "$PROJECT_DIR/ops/backup-redis.sh"
    "$PROJECT_DIR/ops/restore.sh"
    "$PROJECT_DIR/ops/monitor-backups.sh"
)

for script in "${BACKUP_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        log_success "Backup script exists: $(basename "$script")"
    else
        log_error "Backup script NOT found: $(basename "$script")"
    fi
done

if $RUNNING_AS_ROOT; then
    CRON_JOBS=(
        "backup.sh"
        "backup-redis.sh"
        "monitor-backups.sh"
        "certbot renew"
    )

    for job in "${CRON_JOBS[@]}"; do
        if crontab -l 2>/dev/null | grep -q "$job"; then
            log_success "Cron job exists: $job"
        else
            log_error "Cron job NOT found: $job"
        fi
    done
else
    log_warning "Skipping cron job check (not running as root)"
fi

# Check for recent backups
if [ -d "$BACKUP_DIR" ]; then
    DB_BACKUPS=$(find "$BACKUP_DIR" -name "backup_*.sql.gz.gpg" -mtime -1 | wc -l)
    REDIS_BACKUPS=$(find "$BACKUP_DIR" -name "redis_*.rdb.gz.gpg" -mtime -1 | wc -l)

    if [ "$DB_BACKUPS" -gt 0 ]; then
        log_success "Recent database backups found: $DB_BACKUPS"
    else
        log_warning "No recent database backups found"
    fi

    if [ "$REDIS_BACKUPS" -gt 0 ]; then
        log_success "Recent Redis backups found: $REDIS_BACKUPS"
    else
        log_warning "No recent Redis backups found"
    fi
else
    log_warning "Skipping backup file check (backup directory not found)"
fi
echo ""

# 7. API Endpoint Check
echo -e "${BLUE}7. API Endpoint Check${NC}"
echo "----------------------------------------"

API_ENDPOINTS=(
    "https://$API_DOMAIN/health"
    "https://$API_DOMAIN/api/models"
    "https://$API_DOMAIN/docs"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    if curl -sSf -o /dev/null "$endpoint" 2>/dev/null; then
        log_success "API endpoint accessible: $endpoint"
    else
        log_error "API endpoint NOT accessible: $endpoint"
    fi
done
echo ""

# 8. Security Check
echo -e "${BLUE}8. Security Check${NC}"
echo "----------------------------------------"

# Check firewall
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status 2>/dev/null | grep -q "active"; then
        log_success "Firewall is active"

        if sudo ufw status 2>/dev/null | grep -q "80/tcp.*ALLOW"; then
            log_success "Port 80 (HTTP) is open"
        else
            log_error "Port 80 (HTTP) is NOT open"
        fi

        if sudo ufw status 2>/dev/null | grep -q "443/tcp.*ALLOW"; then
            log_success "Port 443 (HTTPS) is open"
        else
            log_error "Port 443 (HTTPS) is NOT open"
        fi

        if sudo ufw status 2>/dev/null | grep -q "22/tcp.*ALLOW"; then
            log_success "Port 22 (SSH) is open"
        else
            log_error "Port 22 (SSH) is NOT open"
        fi
    else
        log_warning "Firewall is NOT active"
    fi
else
    log_warning "UFW firewall not installed"
fi

# Check SSL security headers
SSL_HEADERS=$(curl -sI "https://$API_DOMAIN/health" 2>/dev/null | grep -E "Strict-Transport-Security|X-Content-Type-Options|X-Frame-Options" | wc -l)
if [ "$SSL_HEADERS" -ge 3 ]; then
    log_success "Security headers are properly configured"
else
    log_warning "Security headers may be incomplete"
fi
echo ""

# 9. Performance Check
echo -e "${BLUE}9. Performance Check${NC}"
echo "----------------------------------------"

# Test API response time
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "https://$API_DOMAIN/health" 2>/dev/null)
if [ -n "$RESPONSE_TIME" ]; then
    RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc 2>/dev/null || echo "0")
    if [ "$(echo "$RESPONSE_TIME_MS < 200" | bc)" -eq 1 ]; then
        log_success "API response time: ${RESPONSE_TIME_MS}ms (excellent)"
    elif [ "$(echo "$RESPONSE_TIME_MS < 500" | bc)" -eq 1 ]; then
        log_warning "API response time: ${RESPONSE_TIME_MS}ms (good)"
    else
        log_error "API response time: ${RESPONSE_TIME_MS}ms (needs optimization)"
    fi
else
    log_error "Could not measure API response time"
fi
echo ""

# 10. Log Monitoring Check
echo -e "${BLUE}10. Log Monitoring Check${NC}"
echo "----------------------------------------"

if [ -d "$LOG_DIR" ]; then
    LOG_FILES=("backup.log" "redis-backup.log" "backup-monitor.log" "ssl-monitor.log" "deploy.log")
    for log_file in "${LOG_FILES[@]}"; do
        if [ -f "$LOG_DIR/$log_file" ]; then
            log_success "Log file exists: $log_file"
        else
            log_warning "Log file NOT found: $log_file"
        fi
    done
else
    log_warning "Skipping log file check (log directory not found)"
fi
echo ""

# Summary and Recommendations
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"

# Count success, warning, and error messages
SUCCESS_COUNT=$(grep -c "✅" <<< "$(tail -n 1000)")
WARNING_COUNT=$(grep -c "⚠️" <<< "$(tail -n 1000)")
ERROR_COUNT=$(grep -c "❌" <<< "$(tail -n 1000)")

echo "Results:"
echo "  Success: $SUCCESS_COUNT checks passed"
echo "  Warnings: $WARNING_COUNT checks need attention"
echo "  Errors: $ERROR_COUNT checks failed"
echo ""

if [ "$ERROR_COUNT" -eq 0 ] && [ "$WARNING_COUNT" -le 3 ]; then
    echo -e "${GREEN}🎉 Deployment verification PASSED!${NC}"
    echo ""
    echo "Your AgentsFlowAI deployment is ready for production."
    echo ""
    echo "Next steps:"
    echo "1. Monitor system performance for 24-48 hours"
    echo "2. Set up additional monitoring and alerting"
    echo "3. Test backup restore procedures"
    echo "4. Implement performance optimizations as needed"
    echo "5. Configure CI/CD pipeline for automated deployments"
    echo ""
    echo "Production URL: https://$API_DOMAIN"
    echo "Documentation: https://$API_DOMAIN/docs"
    echo "Health Check: https://$API_DOMAIN/health"
else
    echo -e "${YELLOW}⚠️  Deployment verification completed with issues${NC}"
    echo ""
    echo "Please review the warnings and errors above."
    echo "Critical issues that need immediate attention:"
    echo ""

    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "❌ Critical Errors:"
        grep "❌" <<< "$(tail -n 1000)" | sed 's/^❌ //'
        echo ""
    fi

    if [ "$WARNING_COUNT" -gt 0 ]; then
        echo "⚠️  Warnings to address:"
        grep "⚠️" <<< "$(tail -n 1000)" | sed 's/^⚠️  //'
        echo ""
    fi

    echo "After addressing these issues, run this verification script again."
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Complete${NC}"
echo -e "${BLUE}========================================${NC}"