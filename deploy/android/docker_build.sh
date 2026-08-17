#!/usr/bin/env bash

set -euo pipefail

IMAGE_NAME="boa-android-build"
DOCKERFILE="deploy/android/dockerfile"
WORKDIR="/work"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Please install Docker first." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ ! -f "$ROOT_DIR/$DOCKERFILE" ]]; then
  echo "Dockerfile not found: $ROOT_DIR/$DOCKERFILE" >&2
  exit 1
fi

if [[ "${1:-}" == "--build-only" ]]; then
  docker build -f "$ROOT_DIR/$DOCKERFILE" -t "$IMAGE_NAME" "$ROOT_DIR"
  exit 0
fi

docker build -f "$ROOT_DIR/$DOCKERFILE" -t "$IMAGE_NAME" "$ROOT_DIR"

docker run --rm -it \
  -v "$ROOT_DIR":"$WORKDIR" \
  -w "$WORKDIR" \
  "$IMAGE_NAME" \
  bash -lc "export JAVA_HOME=/opt/java/openjdk-17; export PATH=\$JAVA_HOME/bin:\$PATH; sh deploy/android/setup_devcontainer.sh && . .venv/bin/activate && python deploy/android/build.py all"
