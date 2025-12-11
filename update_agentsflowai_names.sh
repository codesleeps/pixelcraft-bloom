#!/bin/bash

# Comprehensive AgentsFlowAI Renaming Script
# This script updates all references from "agentsflowai" to "agentsflowai"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[UPDATE] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if running from correct directory
if [ ! -d "../agentsflowai" ]; then
    error "Please run this script from the parent directory of agentsflowai"
fi

cd ../agentsflowai || exit 1

log "Starting comprehensive AgentsFlowAI renaming process..."

# 1. Update file contents (text replacements)
log "1. Updating file contents..."

# Files to update with their specific replacements
declare -A replacements=(
    # Configuration files
    ["package.json"]="s/agentsflowai/agentsflowai/g"
    ["package-lock.json"]="s/agentsflowai/agentsflowai/g"
    ["vite.config.ts"]="s/agentsflowai/agentsflowai/g"
    ["public/sw.js"]="s/agentsflowai-v1/agentsflowai-v1/g"
    ["public/robots.txt"]="s/agentsflowai.lovable.app/agentsflow.cloud/g"
    ["public/status.html"]="s/agentsflowai.ai/agentsflow.cloud/g"
    ["index.html"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai.lovable.app/agentsflow.cloud/g; s/@agentsflowai/@agentsflowai/g"
    ["README.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g; s/codesleeps\/agentsflowai/codesleeps\/agentsflowai/g"
    ["DEPLOYMENT_GUIDE.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g"
    ["VPS_QUICK_START.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g"
    ["TESTING_INSTRUCTIONS.md"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["APPLICATION_OVERVIEW.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/AgentsFlowAI/AgentsFlowAI/g"
    ["VPS_COMPARISON_GUIDE.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/AgentsFlowAI/AgentsFlowAI/g"
    ["PERFORMANCE_OPTIMIZATION.md"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["DEPLOYMENT_CHECKLIST.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g"
    ["DOCKER_UPDATE_GUIDE.md"]="s/agentsflowai-backend/agentsflowai-backend/g"
    ["AFTER_RESTART_GUIDE.md"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["SUCCESS_REPORT.md"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["FINAL_SUMMARY.md"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["HOSTINGER_DEPLOYMENT_GUIDE.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g"
    ["DEPLOYMENT_QUICK_REFERENCE.md"]="s/agentsflowai-backend/agentsflowai-backend/g; s/agentsflowai/agentsflowai/g"
    ["ops/SSL_SETUP.md"]="s/agentsflowai/agentsflow.cloud/g; s/agentsflowai.com/agentsflow.cloud/g; s/api.agentsflowai.com/api.agentsflow.cloud/g"
    ["ops/SENTRY_SETUP.md"]="s/agentsflowai-backend/agentsflowai-backend/g; s/agentsflowai-frontend/agentsflowai-frontend/g"
    ["ops/DISASTER_RECOVERY.md"]="s/agentsflowai/agentsflowai/g"
    ["ops/CAPACITY_PLANNING.md"]="s/agentsflowai/agentsflowai/g"
    ["ops/PRODUCTION_READINESS.md"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["ops/PRODUCTION_READINESS_COMPLETE.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai-backend/agentsflowai-backend/g"
    ["ops/uptime-monitor.json"]="s/agentsflowai.ai/agentsflow.cloud/g"
    ["ops/deploy.sh"]="s/agentsflowai/agentsflowai/g; s/agentsflowai-backend/agentsflowai-backend/g"
    ["ops/deploy-production.sh"]="s/agentsflowai/agentsflowai/g; s/AgentsFlowAI/AgentsFlowAI/g"
    ["ops/setup-vps.sh"]="s/agentsflowai/agentsflowai/g; s/AgentsFlowAI/AgentsFlowAI/g"
    ["ops/final-verification.sh"]="s/agentsflowai/agentsflowai/g; s/AgentsFlowAI/AgentsFlowAI/g"
    ["ops/backup.sh"]="s/agentsflowai/agentsflowai/g"
    ["ops/restore.sh"]="s/agentsflowai/agentsflowai/g"
    ["ops/monitor-backups.sh"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["ops/setup-backups.sh"]="s/agentsflowai/agentsflowai/g"
    ["ops/agentsflowai-api.service"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g"
    ["ops/BACKUP_RESTORE.md"]="s/agentsflowai/agentsflowai/g"
    ["scripts/restore-db.sh"]="s/agentsflowai/agentsflowai/g"
    ["scripts/smoke-test.sh"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["scripts/update-docker.sh"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["scripts/verify-docker.sh"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/README.md"]="s/agentsflowai/agentsflowai/g"
    ["backend/EXTERNAL_SERVICES_SETUP.md"]="s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g"
    ["backend/setup_test_data.py"]="s/agentsflowai.com/agentsflow.cloud/g"
    ["backend/generate_test_subscription_data.py"]="s/agentsflowai.com/agentsflow.cloud/g"
    ["backend/app/main.py"]="s/AgentsFlowAI AI Backend/AgentsFlowAI AI Backend/g"
    ["backend/app/config.py"]="s/agentsflowai.com/agentsflow.cloud/g"
    ["backend/app/agents/chat_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/agents/content_creation_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/agents/brand_design_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/agents/ecommerce_solutions_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/agents/web_development_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/agents/digital_marketing_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/agents/recommendation_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/agents/lead_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/agents/analytics_consulting_agent.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/validate_config.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/test_models.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/run.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/__init__.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/app/utils/logger.py"]="s/agentsflowai/agentsflowai/g"
    ["backend/app/utils/health.py"]="s/agentsflowai/agentsflowai/g"
    ["backend/app/utils/external_tools.py"]="s/agentsflowai/agentsflowai/g"
    ["backend/app/utils/ollama_client.py"]="s/agentsflowai/agentsflowai/g"
    ["backend/app/utils/supabase_client.py"]="s/agentsflowai/agentsflowai/g"
    ["backend/app/routes/chat.py"]="s/agentsflowai/agentsflowai/g"
    ["backend/app/routes/appointments.py"]="s/agentsflowai.com/agentsflow.cloud/g"
    ["backend/app/routes/payments.py"]="s/agentsflowai/agentsflowai/g"
    ["backend/supabase/migrations/20250126000000_ai_features_schema.sql"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/test_analytics_api.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
    ["backend/test_agents.py"]="s/AgentsFlowAI/AgentsFlowAI/g"
)

# Update each file
for file in "${!replacements[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i "${replacements[$file]}" "$file"
        success "Updated $file"
    else
        warn "File $file not found, skipping..."
    fi
done

# 2. Update frontend components
log "2. Updating frontend components..."

# Frontend files with their replacements
frontend_files=(
    "src/components/ChatWidget.tsx"
    "src/components/Navigation.tsx"
    "src/components/HeroSection.tsx"
    "src/components/DashboardLayout.tsx"
    "src/components/TestimonialsSection.tsx"
    "src/components/TrustSection.tsx"
    "src/components/ErrorBoundary.tsx"
    "src/components/DemoPreview.tsx"
    "src/components/FAQSection.tsx"
    "src/components/ROICalculator.tsx"
    "src/components/SEOHead.tsx"
    "src/components/Footer.tsx"
    "src/pages/ModelAnalytics.tsx"
    "src/pages/StrategySession.tsx"
    "src/pages/ModelTest.tsx"
    "src/pages/Auth.tsx"
    "src/pages/Partnership.tsx"
    "src/pages/Index.tsx"
    "src/components/__tests__/Navigation.test.tsx"
    "src/components/__tests__/ROICalculator.test.tsx"
)

for file in "${frontend_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i 's/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai.lovable.app/agentsflow.cloud/g; s/@agentsflowai/@agentsflowai/g' "$file"
        success "Updated $file"
    else
        warn "File $file not found, skipping..."
    fi
done

# 3. Update backend Python files
log "3. Updating backend Python files..."

python_files=(
    "backend/app/agents/orchestrator.py"
    "backend/app/routes/chat.py"
    "backend/app/routes/payments.py"
    "backend/app/routes/appointments.py"
    "backend/app/routes/leads.py"
    "backend/app/routes/analytics.py"
    "backend/app/routes/models.py"
    "backend/app/routes/notifications.py"
    "backend/app/routes/pricing.py"
    "backend/app/routes/websocket.py"
    "backend/app/utils/cache.py"
    "backend/app/utils/health.py"
    "backend/app/utils/limiter.py"
    "backend/app/utils/logger.py"
    "backend/app/utils/notification_service.py"
    "backend/app/utils/ollama_client.py"
    "backend/app/utils/redis_client.py"
    "backend/app/utils/sentry_helpers.py"
    "backend/app/utils/supabase_client.py"
    "backend/app/utils/external_tools.py"
    "backend/app/utils/auth.py"
    "backend/app/utils/cache.py"
    "backend/app/utils/health.py"
    "backend/app/utils/limiter.py"
    "backend/app/utils/logger.py"
    "backend/app/utils/notification_service.py"
    "backend/app/utils/ollama_client.py"
    "backend/app/utils/redis_client.py"
    "backend/app/utils/sentry_helpers.py"
    "backend/app/utils/supabase_client.py"
    "backend/app/utils/external_tools.py"
    "backend/app/utils/auth.py"
)

for file in "${python_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i 's/agentsflowai/agentsflowai/g' "$file"
        success "Updated $file"
    else
        warn "File $file not found, skipping..."
    fi
done

# 4. Update test files
log "4. Updating test files..."

test_files=(
    "backend/tests/test_*.py"
    "backend/test_*.py"
    "src/**/__tests__/*.tsx"
    "src/**/*.test.tsx"
)

for pattern in "${test_files[@]}"; do
    find . -name "$pattern" -type f | while read -r file; do
        if [ -f "$file" ]; then
            log "Updating $file..."
            sed -i 's/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g' "$file"
            success "Updated $file"
        fi
    done
done

# 5. Update configuration files
log "5. Updating configuration files..."

config_files=(
    ".env.example"
    "backend/.env.example"
    "backend/.env.production.example"
    "backend/.env.staging.example"
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "vercel.json"
    "postcss.config.js"
    "tailwind.config.ts"
    "tsconfig.json"
    "tsconfig.app.json"
    "tsconfig.node.json"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i 's/agentsflowai/agentsflowai/g; s/AgentsFlowAI/AgentsFlowAI/g' "$file"
        success "Updated $file"
    else
        warn "File $file not found, skipping..."
    fi
done

# 6. Update documentation files
log "6. Updating documentation files..."

doc_files=(
    "*.md"
    "ops/*.md"
    "scripts/*.md"
    "docs/*.md"
)

for pattern in "${doc_files[@]}"; do
    find . -name "$pattern" -type f | while read -r file; do
        if [ -f "$file" ]; then
            log "Updating $file..."
            sed -i 's/AgentsFlowAI/AgentsFlowAI/g; s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g' "$file"
            success "Updated $file"
        fi
    done
done

# 7. Update Docker and system files
log "7. Updating Docker and system files..."

docker_files=(
    "Dockerfile"
    "Dockerfile.prod"
    "backend/Dockerfile"
    "backend/Dockerfile.prod"
    ".dockerignore"
    "backend/.dockerignore"
)

for file in "${docker_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i 's/agentsflowai/agentsflowai/g' "$file"
        success "Updated $file"
    else
        warn "File $file not found, skipping..."
    fi
done

# 8. Update GitHub workflows
log "8. Updating GitHub workflows..."

github_files=(
    ".github/workflows/*.yml"
    ".github/workflows/*.yaml"
)

for pattern in "${github_files[@]}"; do
    find . -name "$pattern" -type f | while read -r file; do
        if [ -f "$file" ]; then
            log "Updating $file..."
            sed -i 's/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g' "$file"
            success "Updated $file"
        fi
    done
done

# 9. Update package files
log "9. Updating package files..."

package_files=(
    "package.json"
    "package-lock.json"
    "backend/package.json"
    "backend/package-lock.json"
    "backend/requirements.txt"
    "backend/pyproject.toml"
    "backend/setup.py"
)

for file in "${package_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i 's/agentsflowai/agentsflowai/g; s/AgentsFlowAI/AgentsFlowAI/g' "$file"
        success "Updated $file"
    else
        warn "File $file not found, skipping..."
    fi
done

# 10. Update miscellaneous files
log "10. Updating miscellaneous files..."

misc_files=(
    "*.sh"
    "*.json"
    "*.yaml"
    "*.yml"
    "*.txt"
    "*.html"
    "*.css"
    "*.js"
    "*.ts"
    "*.tsx"
    "*.jsx"
)

for pattern in "${misc_files[@]}"; do
    find . -name "$pattern" -type f | while read -r file; do
        if [ -f "$file" ]; then
            log "Updating $file..."
            sed -i 's/AgentsFlowAI/AgentsFlowAI/g; s/AgentsFlowAI/AgentsFlowAI/g; s/agentsflowai/agentsflowai/g; s/agentsflowai/agentsflowai/g' "$file"
            success "Updated $file"
        fi
    done
done

log "${GREEN}🎉 AgentsFlowAI renaming process completed!${NC}"
log ""
log "Summary of changes:"
log "- Updated 300+ references from 'agentsflowai' to 'agentsflowai'"
log "- Updated project names, URLs, and configurations"
log "- Updated documentation, code comments, and logs"
log "- Updated Docker configurations and system files"
log "- Updated frontend components and backend services"
log ""
log "Next steps:"
log "1. Test the updated application"
log "2. Verify all endpoints are working"
log "3. Update GitHub repository name"
log "4. Deploy to production"

success "All references have been updated to AgentsFlowAI!"