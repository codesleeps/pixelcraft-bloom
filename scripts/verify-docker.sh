#!/bin/bash
# Docker verification script for AgentsFlowAI

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "AgentsFlowAI - Docker Verification"
echo "=========================================="
echo ""

# Check if Docker is running
echo "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo ""
    echo "Please start Docker Desktop:"
    echo "  macOS: open -a Docker"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check containers
echo "Checking containers..."
docker compose ps
echo ""

# Check if backend is running
if docker compose ps backend | grep -q "Up"; then
    echo -e "${GREEN}✓ Backend container is running${NC}"
    echo ""
    
    # Test endpoints
    echo "Testing endpoints..."
    sleep 5
    
    echo "1. Health endpoint:"
    curl -s http://localhost:8000/health | python3 -m json.tool || echo "Failed"
    echo ""
    
    echo "2. Models list:"
    curl -s http://localhost:8000/api/models | python3 -m json.tool || echo "Failed"
    echo ""
    
    echo "3. Specific model:"
    curl -s http://localhost:8000/api/models/mistral | python3 -m json.tool || echo "Failed"
    echo ""
    
    echo -e "${GREEN}✓ Docker verification complete!${NC}"
else
    echo -e "${YELLOW}⚠ Backend container not running${NC}"
    echo ""
    echo "To start Docker services:"
    echo "  ./scripts/update-docker.sh"
    echo ""
    echo "Or manually:"
    echo "  docker compose up -d"
fi

echo ""
echo "=========================================="
