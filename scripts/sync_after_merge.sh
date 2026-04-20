#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/sync_after_merge.sh [remote-url]
# Example:
#   bash scripts/sync_after_merge.sh https://github.com/JeonghaedongVis/EventSptool.git

REMOTE_URL="${1:-}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository." >&2
  exit 1
fi

if [[ -n "$REMOTE_URL" ]]; then
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE_URL"
  else
    git remote add origin "$REMOTE_URL"
  fi
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "origin remote is not configured. Pass remote URL as first argument." >&2
  exit 1
fi

git fetch origin --prune

if git show-ref --verify --quiet refs/remotes/origin/main; then
  git checkout -B main origin/main
  git pull --ff-only origin main
else
  echo "origin/main not found. Please check remote branch name." >&2
  exit 1
fi

echo "Sync complete. Current branch: $(git branch --show-current)"
git log --oneline -n 3
