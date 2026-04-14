#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/sites/wb}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-flask.service}"
RUN_TESTS="${RUN_TESTS:-1}"
RELOAD_NGINX="${RELOAD_NGINX:-1}"

run_as_root() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    else
        sudo "$@"
    fi
}

log() {
    printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

if [ ! -d "$APP_DIR/.git" ]; then
    echo "Repository not found: $APP_DIR" >&2
    exit 1
fi

cd "$APP_DIR"

if ! git diff-index --quiet HEAD --; then
    echo "Refusing to deploy with local tracked changes in $APP_DIR" >&2
    git status --short
    exit 1
fi

log "Updating git branch $BRANCH"
git fetch origin "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [ ! -x .venv/bin/python ]; then
    log "Creating virtual environment"
    python3 -m venv .venv
fi

log "Installing Python dependencies"
.venv/bin/pip install -r requirements.txt

log "Ensuring runtime directories exist"
mkdir -p var/cache var/generated

if [ "$RUN_TESTS" = "1" ]; then
    log "Running tests"
    .venv/bin/python -m unittest
fi

log "Reloading systemd configuration"
run_as_root systemctl daemon-reload

log "Restarting service $SERVICE_NAME"
run_as_root systemctl restart "$SERVICE_NAME"
run_as_root systemctl status --no-pager "$SERVICE_NAME"

if [ "$RELOAD_NGINX" = "1" ]; then
    log "Validating nginx configuration"
    run_as_root nginx -t

    log "Reloading nginx"
    run_as_root systemctl reload nginx
fi

log "Deployment finished"
