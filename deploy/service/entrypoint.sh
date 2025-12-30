#!/bin/sh
set -e

APP_DIR="/app"
REPO_URL="https://gitee.com/Kiramei/baas-dev.git"
BRANCH="master"

cd "$APP_DIR"

if [ ! -d ".git" ]; then
    echo "[INFO] No git repository found. Cloning repository..."
    git clone "$REPO_URL" . \
        --branch "$BRANCH" \
        --depth 1
else
    echo "[INFO] Git repository found. Pulling latest changes..."
    git fetch origin "$BRANCH"
    git checkout "$BRANCH"
    git pull --ff-only origin "$BRANCH"
fi

echo "[INFO] Starting service..."
export GIT_SSL_CAINFO=/etc/ssl/certs/ca-certificates.crt
exec /opt/venv/bin/python main.service.py --host 0.0.0.0
