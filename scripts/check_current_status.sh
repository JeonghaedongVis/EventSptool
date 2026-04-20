#!/usr/bin/env bash
set -euo pipefail

echo "== Git basics =="
git rev-parse --is-inside-work-tree >/dev/null
echo "branch: $(git branch --show-current)"
echo ""
echo "== remotes =="
git remote -v || true
echo ""
echo "== local recent commits =="
git log --oneline -n 5 || true
echo ""
echo "== remote heads (if origin exists) =="
if git remote get-url origin >/dev/null 2>&1; then
  git ls-remote --heads origin || true
else
  echo "origin not configured"
fi
echo ""
echo "== key artifact files =="
for f in \
  docs/event-crm-blueprint-ko.md \
  docs/event-crm-implementation-playbook-ko.md \
  ops/make/make-scenario-io-spec-ko.md \
  ops/make/module-field-mapping.csv \
  scripts/validate_ops_artifacts.py
  do
  if [[ -f "$f" ]]; then echo "[OK] $f"; else echo "[MISS] $f"; fi
done

echo ""
echo "== validation =="
python3 scripts/validate_ops_artifacts.py
