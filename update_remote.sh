#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/sites/wb}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-flask.service}"
DEPLOY_USER="${DEPLOY_USER:-${SUDO_USER:-$(id -un)}}"
VENV_DIR="${VENV_DIR:-.venv}"
RUN_TESTS="${RUN_TESTS:-1}"
RELOAD_NGINX="${RELOAD_NGINX:-1}"

run_as_root() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    else
        sudo "$@"
    fi
}

run_in_app_dir_as_deploy_user() {
    if [ "$(id -un)" = "$DEPLOY_USER" ]; then
        (
            cd "$APP_DIR"
            "$@"
        )
    else
        sudo -H -u "$DEPLOY_USER" bash -lc "cd '$APP_DIR' && $*"
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

if ! run_in_app_dir_as_deploy_user git diff-index --quiet HEAD --; then
    echo "Refusing to deploy with local tracked changes in $APP_DIR" >&2
    run_in_app_dir_as_deploy_user git status --short
    exit 1
fi

log "Updating git branch $BRANCH as $DEPLOY_USER"
run_in_app_dir_as_deploy_user git fetch origin "$BRANCH"
run_in_app_dir_as_deploy_user git pull --ff-only origin "$BRANCH"

if ! run_in_app_dir_as_deploy_user test -x "$VENV_DIR/bin/python"; then
    log "Creating virtual environment"
    run_in_app_dir_as_deploy_user python3 -m venv "$VENV_DIR"
fi

log "Installing Python dependencies"
run_in_app_dir_as_deploy_user "$VENV_DIR/bin/pip" install -r requirements.txt

log "Ensuring runtime directories exist"
run_in_app_dir_as_deploy_user mkdir -p var/cache var/generated

if [ "$RUN_TESTS" = "1" ]; then
    log "Running tests"
    run_in_app_dir_as_deploy_user "$VENV_DIR/bin/python" -m unittest
fi

log "Reloading systemd configuration"
run_as_root systemctl daemon-reload

log "Restarting service $SERVICE_NAME"
run_as_root systemctl restart "$SERVICE_NAME"
run_as_root systemctl status --no-pager -l "$SERVICE_NAME"
if ! run_as_root systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Service $SERVICE_NAME is not active after restart" >&2
    run_as_root journalctl -u "$SERVICE_NAME" -n 80 --no-pager
    exit 1
fi

if [ "$RELOAD_NGINX" = "1" ]; then
    log "Validating nginx configuration"
    run_as_root nginx -t

    log "Reloading nginx"
    run_as_root systemctl reload nginx
fi

log "Deployment finished"
