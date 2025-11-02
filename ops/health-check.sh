#!/bin/bash
set -euo pipefail

# Simple health-check utility for the API
# Usage: ./ops/health-check.sh https://api.yourdomain.com/health

URL=${1:-"https://api.yourdomain.com/health"}

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

status=$(curl -sk -o /dev/null -w "%{http_code}" "$URL" || true)
if [[ "$status" == "200" ]]; then
  echo -e "${GREEN}Health OK (200)${NC}"
  exit 0
else
  echo -e "${RED}Health FAILED ($status)${NC}"
  exit 1
fi

