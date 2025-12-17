#!/bin/bash

# Targeted AgentsFlowAI Renaming Script
# This script updates ONLY the files that actually contain "pixelcraft" references
# Much more efficient than processing thousands of files

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

log "Starting targeted AgentsFlowAI renaming process..."

# 1. Find files that actually contain "pixelcraft" references (excluding node_modules)
log "1. Finding files that contain 'pixelcraft' references..."

# Use grep to find files that actually contain the references we want to replace
files_to_update=$(grep -rl --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist --exclude-dir=build "pixelcraft\|PixelCraft" . 2>/dev/null | head -50)

if [ -z "$files_to_update" ]; then
    log "No files found containing 'pixelcraft' or 'PixelCraft' references."
    success "Targeted update completed - no changes needed."
    exit 0
fi

log "Found $(echo "$files_to_update" | wc -l) files to update:"

# 2. Update each file individually
file_count=0
updated_count=0

for file in $files_to_update; do
    if [ -f "$file" ]; then
        ((file_count++))

        # Skip binary files
        if file "$file" | grep -q "text"; then
            log "Updating $file..."

            # Make a backup
            cp "$file" "$file.bak"

            # Update the file
            sed -i '' \
                -e 's/PixelCraft Bloom/AgentsFlowAI/g' \
                -e 's/PixelCraft/AgentsFlowAI/g' \
                -e 's/pixelcraft-bloom/agentsflowai/g' \
                -e 's/pixelcraft/agentsflowai/g' \
                -e 's/pixelcraft.lovable.app/agentsflow.cloud/g' \
                -e 's/pixelcraft.ai/agentsflow.cloud/g' \
                -e 's/@pixelcraft/@agentsflowai/g' \
                "$file"

            # Check if the file was actually modified
            if ! diff -q "$file" "$file.bak" >/dev/null 2>&1; then
                ((updated_count++))
                success "Updated $file"
                rm "$file.bak"
            else
                warn "No changes made to $file (already updated or no matches)"
                rm "$file.bak"
            fi
        else
            warn "Skipping binary file: $file"
        fi
    fi
done

# 3. Special handling for specific files that we know need updates
log "2. Updating specific known files..."

# Update package.json and package-lock.json
for file in package.json package-lock.json; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i '' 's/"name": "pixelcraft-bloom"/"name": "agentsflowai"/' "$file"
        sed -i '' 's/pixelcraft-bloom/agentsflowai/g' "$file"
        success "Updated $file"
    fi
done

# Update Docker and configuration files
for file in Dockerfile Dockerfile.prod docker-compose.yml docker-compose.prod.yml; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i '' 's/pixelcraft-bloom/agentsflowai/g' "$file"
        success "Updated $file"
    fi
done

# Update backend configuration
if [ -f "backend/package.json" ]; then
    log "Updating backend/package.json..."
    sed -i '' 's/"name": "pixelcraft-bloom"/"name": "agentsflowai"/' "backend/package.json"
    success "Updated backend/package.json"
fi

# Update GitHub workflows
if [ -d ".github/workflows" ]; then
    for file in .github/workflows/*.yml .github/workflows/*.yaml; do
        if [ -f "$file" ]; then
            log "Updating $file..."
            sed -i '' 's/PixelCraft Bloom/AgentsFlowAI/g' "$file"
            sed -i '' 's/pixelcraft-bloom/agentsflowai/g' "$file"
            success "Updated $file"
        fi
    done
fi

# 4. Update specific backend files
log "3. Updating backend files..."

backend_files=(
    "backend/app/main.py"
    "backend/app/config.py"
    "backend/app/__init__.py"
    "backend/app/utils/logger.py"
    "backend/app/utils/health.py"
    "backend/app/utils/external_tools.py"
    "backend/app/utils/ollama_client.py"
    "backend/app/utils/supabase_client.py"
    "backend/app/routes/chat.py"
    "backend/app/routes/appointments.py"
    "backend/app/routes/payments.py"
    "backend/app/agents/chat_agent.py"
    "backend/app/agents/content_creation_agent.py"
    "backend/app/agents/brand_design_agent.py"
    "backend/app/agents/ecommerce_solutions_agent.py"
    "backend/app/agents/web_development_agent.py"
    "backend/app/agents/digital_marketing_agent.py"
    "backend/app/agents/recommendation_agent.py"
    "backend/app/agents/lead_agent.py"
    "backend/app/agents/analytics_consulting_agent.py"
    "backend/validate_config.py"
    "backend/test_models.py"
    "backend/run.py"
)

for file in "${backend_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i '' 's/PixelCraft/AgentsFlowAI/g' "$file"
        sed -i '' 's/pixelcraft/agentsflowai/g' "$file"
        success "Updated $file"
    fi
done

# 5. Update frontend files
log "4. Updating frontend files..."

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
    "index.html"
)

for file in "${frontend_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i '' 's/PixelCraft/AgentsFlowAI/g' "$file"
        sed -i '' 's/pixelcraft.lovable.app/agentsflow.cloud/g' "$file"
        sed -i '' 's/@pixelcraft/@agentsflowai/g' "$file"
        success "Updated $file"
    fi
done

# 6. Update documentation files
log "5. Updating documentation files..."

doc_files=(
    "README.md"
    "DEPLOYMENT_GUIDE.md"
    "TESTING_INSTRUCTIONS.md"
    "APPLICATION_OVERVIEW.md"
    "VPS_COMPARISON_GUIDE.md"
    "PERFORMANCE_OPTIMIZATION.md"
    "DEPLOYMENT_CHECKLIST.md"
    "DOCKER_UPDATE_GUIDE.md"
    "AFTER_RESTART_GUIDE.md"
    "SUCCESS_REPORT.md"
    "FINAL_SUMMARY.md"
    "HOSTINGER_DEPLOYMENT_GUIDE.md"
    "DEPLOYMENT_QUICK_REFERENCE.md"
    "ops/SSL_SETUP.md"
    "ops/SENTRY_SETUP.md"
    "ops/DISASTER_RECOVERY.md"
    "ops/CAPACITY_PLANNING.md"
    "ops/PRODUCTION_READINESS.md"
    "ops/PRODUCTION_READINESS_COMPLETE.md"
    "ops/BACKUP_RESTORE.md"
    "ops/CAPACITY_PLANNING.md"
    "backend/README.md"
    "backend/EXTERNAL_SERVICES_SETUP.md"
)

for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i '' 's/PixelCraft Bloom/AgentsFlowAI/g' "$file"
        sed -i '' 's/PixelCraft/AgentsFlowAI/g' "$file"
        sed -i '' 's/pixelcraft-bloom/agentsflowai/g' "$file"
        sed -i '' 's/pixelcraft/agentsflowai/g' "$file"
        success "Updated $file"
    fi
done

# 7. Update ops scripts
log "6. Updating operations scripts..."

ops_files=(
    "ops/deploy.sh"
    "ops/deploy-production.sh"
    "ops/setup-vps.sh"
    "ops/final-verification.sh"
    "ops/backup.sh"
    "ops/restore.sh"
    "ops/monitor-backups.sh"
    "ops/setup-backups.sh"
    "ops/pixelcraft-api.service"
    "ops/backup-redis.sh"
    "ops/vps-deploy.sh"
    "scripts/restore-db.sh"
    "scripts/smoke-test.sh"
    "scripts/update-docker.sh"
    "scripts/verify-docker.sh"
)

for file in "${ops_files[@]}"; do
    if [ -f "$file" ]; then
        log "Updating $file..."
        sed -i '' 's/pixelcraft-bloom/agentsflowai/g' "$file"
        sed -i '' 's/PixelCraft Bloom/AgentsFlowAI/g' "$file"
        success "Updated $file"
    fi
done

log "${GREEN}🎉 Targeted AgentsFlowAI renaming process completed!${NC}"
log ""
log "Summary:"
log "- Processed $file_count files"
log "- Updated $updated_count files with changes"
log "- Skipped binary files and node_modules"
log "- Focused on source code, configuration, and documentation"
log ""
log "Next steps:"
log "1. Test the updated application"
log "2. Verify all endpoints are working"
log "3. Update GitHub repository name"
log "4. Deploy to production"

success "Targeted update completed efficiently!"