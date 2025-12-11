#!/bin/bash

# AgentsFlowAI - Smoke Test Script
# Tests health check, models endpoint, and chat endpoint
# Run with: ./scripts/smoke-test.sh or bash scripts/smoke-test.sh

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
TIMEOUT="${TIMEOUT:-60}"
RETRIES="${RETRIES:-3}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "AgentsFlowAI - Smoke Test"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Timeout: ${TIMEOUT}s per request"
echo "Retries: $RETRIES attempts"
echo ""

# Test counter
PASSED=0
FAILED=0

# Function to test an endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_field=$5
    
    echo -n "Testing $name... "
    
    local attempt=1
    while [ $attempt -le $RETRIES ]; do
        if [ "$method" = "GET" ]; then
            response=$(curl -s --max-time $TIMEOUT -X GET "$BASE_URL$endpoint")
        else
            response=$(curl -s --max-time $TIMEOUT -X POST "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data")
        fi
        
        if [ $? -eq 0 ]; then
            # Check if response is valid JSON
            if echo "$response" | jq empty 2>/dev/null; then
                # Check if expected field exists (if specified)
                if [ -z "$expected_field" ] || echo "$response" | jq -e "$expected_field" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ PASS${NC}"
                    PASSED=$((PASSED + 1))
                    return 0
                fi
            fi
        fi
        
        # Retry on failure
        if [ $attempt -lt $RETRIES ]; then
            echo -n "retry($attempt/$RETRIES)... "
            sleep 3
        fi
        attempt=$((attempt + 1))
    done
    
    # All retries exhausted
    echo -e "${RED}✗ FAIL${NC}"
    FAILED=$((FAILED + 1))
    return 1
}

# Test 1: Health Check (simple endpoint that should always work)
echo "--- Test 1: Health Check ---"
test_endpoint "Health Check" "GET" "/health" "" "" || true

# Test 2: Models Endpoint (lists available models)
echo ""
echo "--- Test 2: Models Endpoint ---"
test_endpoint "Models List" "GET" "/api/models" "" ".models" || true

# Test 3: Chat Endpoint (requires model inference)
# Note: This may fail if Ollama is still loading the model on first request
# Retry up to 3 times with 30s timeout
echo ""
echo "--- Test 3: Chat Endpoint ---"
TIMEOUT=90 test_endpoint "Chat Message" "POST" "/api/chat/message" \
    '{"message":"Say hello in one sentence"}' \
    ".response" || true

# Test 4: Models Details Endpoint (get specific model info)
echo ""
echo "--- Test 4: Model Details ---"
test_endpoint "Model Details" "GET" "/api/models/mistral" "" ".name" || true

# Summary
echo ""
echo "=========================================="
echo "Test Results:"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
