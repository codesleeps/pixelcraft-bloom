#!/bin/bash
set -euo pipefail

# AgentsFlowAI - Zero(ish)-downtime deploy script
# Usage: sudo ./ops/deploy.sh [branch]
# Defaults: BRANCH=main

BRANCH=${1:-main}
APP_DIR="/opt/agentsflowai"
SERVICE_NAME="pixelcraft-api"
ENV_PATH="$APP_DIR/backend/.env"
VENV_PATH="$APP_DIR/backend/.venv"
REQUIREMENTS_PATH="$APP_DIR/backend/requirements.txt"
HEALTH_URL="https://api.yourdomain.com/health"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
err() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"; }

require_root() {
  if [[ $EUID -ne 0 ]]; then
    err "Run as root (use sudo)"; exit 1;
  fi
}

check_prereqs() {
  [[ -d "$APP_DIR" ]] || { err "App dir $APP_DIR missing"; exit 1; }
  [[ -f "$ENV_PATH" ]] || { err "Env file $ENV_PATH missing"; exit 1; }
  command -v systemctl >/dev/null || { err "systemctl not found"; exit 1; }
}

git_update() {
  log "Updating code from branch $BRANCH..."
  cd "$APP_DIR"
  if [[ -d .git ]]; then
    git fetch --all --prune
    git checkout "$BRANCH"
    git pull --ff-only origin "$BRANCH"
  else
    warn "No git repo detected at $APP_DIR; skipping git pull"
  fi
}

ensure_venv() {
  if [[ ! -d "$VENV_PATH" ]]; then
    log "Creating Python venv..."
    python3 -m venv "$VENV_PATH"
  fi
  "$VENV_PATH/bin/pip" install --upgrade pip wheel
}

install_deps() {
  if [[ -f "$REQUIREMENTS_PATH" ]]; then
    log "Installing backend dependencies..."
    "$VENV_PATH/bin/pip" install -r "$REQUIREMENTS_PATH"
  else
    warn "No requirements.txt found; skipping dependency install"
  fi
}

restart_service() {
  log "Restarting service $SERVICE_NAME..."
  systemctl restart "$SERVICE_NAME"
}

health_check() {
  log "Checking health at $HEALTH_URL..."
  local tries=30
  for i in $(seq 1 $tries); do
    status=$(curl -sk -o /dev/null -w "%{http_code}" "$HEALTH_URL" || true)
    if [[ "$status" == "200" ]]; then
      log "Health OK (200)"
      return 0
    fi
    sleep 2
  done
  err "Health check failed after $tries attempts"
  return 1
}

main() {
  require_root
  check_prereqs
  git_update
  ensure_venv
  install_deps

  # Attempt graceful restart
  restart_service
  if ! health_check; then
    warn "Retrying restart..."
    restart_service
    health_check || { err "Deployment failed"; exit 1; }
  fi

  log "Deployment successful"
}

main "$@"

