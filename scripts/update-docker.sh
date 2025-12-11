#!/bin/bash
# AgentsFlowAI - Docker Update Script
# Updates Docker images to match local code changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "AgentsFlowAI - Docker Update Script"
echo -e "==========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo ""
    echo "Please start Docker Desktop and try again:"
    echo "  macOS: open -a Docker"
    echo "  Linux: sudo systemctl start docker"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found in project root${NC}"
    if [ -f "backend/.env" ]; then
        echo "Copying backend/.env to project root..."
        cp backend/.env .env
        echo -e "${GREEN}✓ .env file created${NC}"
    else
        echo -e "${RED}✗ No .env file found${NC}"
        echo "Please create .env file with required configuration"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

# Verify .env has correct format
echo "Checking .env configuration..."
if grep -q "SUPABASE__URL" .env && grep -q "SUPABASE__KEY" .env; then
    echo -e "${GREEN}✓ .env has correct nested configuration format${NC}"
else
    echo -e "${YELLOW}⚠ .env may need updating for nested configuration${NC}"
    echo "  Ensure you have:"
    echo "    SUPABASE__URL=..."
    echo "    SUPABASE__KEY=..."
    echo "    SUPABASE__JWT_SECRET=..."
    echo ""
fi

# Stop running containers
echo ""
echo "Stopping running containers..."
docker compose down
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Rebuild backend image
echo "Rebuilding backend image..."
echo -e "${BLUE}This may take a few minutes...${NC}"
echo ""

if docker compose build backend; then
    echo ""
    echo -e "${GREEN}✓ Backend image rebuilt successfully${NC}"
else
    echo ""
    echo -e "${RED}✗ Failed to rebuild backend image${NC}"
    exit 1
fi

# Start services
echo ""
echo "Starting services with updated images..."
docker compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Check if backend is running
if docker compose ps backend | grep -q "Up"; then
    echo -e "${GREEN}✓ Backend container is running${NC}"
else
    echo -e "${RED}✗ Backend container failed to start${NC}"
    echo ""
    echo "Check logs with: docker compose logs backend"
    exit 1
fi

# Test health endpoint
echo ""
echo "Testing health endpoint..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Health endpoint responding${NC}"
else
    echo -e "${YELLOW}⚠ Health endpoint not responding yet${NC}"
    echo "  Waiting 10 more seconds..."
    sleep 10
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Health endpoint responding${NC}"
    else
        echo -e "${RED}✗ Health endpoint not responding${NC}"
        echo ""
        echo "Check logs with: docker compose logs backend"
    fi
fi

# Test model endpoints
echo ""
echo "Testing model endpoints..."
if curl -s http://localhost:8000/api/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Model endpoints responding${NC}"
    
    # Check if models show health: true
    RESPONSE=$(curl -s http://localhost:8000/api/models)
    if echo "$RESPONSE" | grep -q '"health": true'; then
        echo -e "${GREEN}✓ Models showing health: true${NC}"
    else
        echo -e "${YELLOW}⚠ Models may not be healthy${NC}"
        echo "  This is expected if Ollama is not running"
    fi
else
    echo -e "${RED}✗ Model endpoints not responding${NC}"
    echo ""
    echo "Check logs with: docker compose logs backend"
fi

# Summary
echo ""
echo -e "${BLUE}=========================================="
echo "Update Summary"
echo -e "==========================================${NC}"
echo ""
echo "Services status:"
docker compose ps
echo ""

echo -e "${GREEN}✓ Docker images updated successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. View logs: docker compose logs -f backend"
echo "  2. Test endpoints:"
echo "     curl http://localhost:8000/health"
echo "     curl http://localhost:8000/api/models"
echo "  3. Pull Ollama models (if needed):"
echo "     docker compose exec ollama ollama pull mistral:7b"
echo "     docker compose exec ollama ollama pull mixtral:8x7b"
echo ""
echo "For more information, see: DOCKER_UPDATE_GUIDE.md"
echo ""
