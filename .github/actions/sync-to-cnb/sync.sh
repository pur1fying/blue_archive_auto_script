#!/usr/bin/env bash
set -euo pipefail

if [[ ! "${CNB_REPO_URL:-}" =~ ^https://cnb\.cool/[A-Za-z0-9._/-]+$ ]]; then
  echo "::error::CNB_REPO_URL must be an HTTPS repository URL on cnb.cool."
  exit 1
fi
if [[ -z "${CNB_SYNC_TOKEN:-}" ]]; then
  echo "::error::The CNB sync token is missing. Configure the secret for this repository."
  exit 1
fi

# Fetch after acquiring the workflow's concurrency slot. Only mirror public
# branches and tags, excluding origin/HEAD and GitHub pull-request refs.
git fetch --no-tags --prune origin \
  '+refs/heads/*:refs/cnb-sync/heads/*' \
  '+refs/tags/*:refs/cnb-sync/tags/*'

cnb_auth=$(printf 'cnb:%s' "$CNB_SYNC_TOKEN" | base64 -w 0)
echo "::add-mask::$cnb_auth"
# Ordinary pushes reject divergent refs. Never force or delete CNB-only refs.
git -c "http.https://cnb.cool/.extraheader=AUTHORIZATION: basic $cnb_auth" \
  push "$CNB_REPO_URL" \
  'refs/cnb-sync/heads/*:refs/heads/*' \
  'refs/cnb-sync/tags/*:refs/tags/*'
