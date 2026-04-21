#!/usr/bin/env bash
set -euo pipefail

BRANCH_NAME="${1:-feat/event-crm-update}"

git checkout main
git pull origin main --ff-only
git checkout -b "$BRANCH_NAME"

echo "[OK] Created and switched to $BRANCH_NAME"
echo "Next: git add . && git commit -m \"feat: ...\" && git push -u origin $BRANCH_NAME"
