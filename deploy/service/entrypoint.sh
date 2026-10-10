#!/bin/sh
set -e

APP_DIR="/app"
REPO_URL="https://gitee.com/Kiramei/baas-dev.git"
BRANCH="master"

cd "$APP_DIR"

setup_no_update() {
    if [ ! -f "setup.toml" ]; then
        return 1
    fi
    value="$(awk '
        /^\[.*\]$/ { section=$0 }
        (section == "[General]" || section == "[general]") {
            line=$0
            gsub(/[[:space:]]/, "", line)
            split(line, parts, "=")
            if (parts[1] == "no_update") {
                print tolower(parts[2])
                exit
            }
        }
    ' setup.toml)"
    [ "$value" = "true" ]
}

if setup_no_update; then
    echo "[INFO] no_update is enabled. Skipping repository update."
elif [ ! -d ".git" ]; then
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
