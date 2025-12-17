#!/bin/bash
# Quick verification script for PixelCraft Bloom

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "PixelCraft Bloom - Local Verification"
echo "=========================================="
echo ""

# Check if backend is running
echo "Checking if backend is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
    echo ""
    
    # Test health endpoint
    echo "Testing /health endpoint..."
    curl -s http://localhost:8000/health | python3 -m json.tool
    echo ""
    
    # Test models endpoint
    echo "Testing /api/models endpoint..."
    curl -s http://localhost:8000/api/models | python3 -m json.tool
    echo ""
    
    # Test specific model
    echo "Testing /api/models/mistral endpoint..."
    curl -s http://localhost:8000/api/models/mistral | python3 -m json.tool
    echo ""
    
    echo -e "${GREEN}✓ All endpoints working!${NC}"
else
    echo -e "${YELLOW}⚠ Backend not running${NC}"
    echo ""
    echo "To start backend locally:"
    echo "  cd backend"
    echo "  python -m uvicorn app.main:app --reload"
    echo ""
    echo "Or use Docker:"
    echo "  ./scripts/update-docker.sh"
fi

echo ""
echo "=========================================="
