$ErrorActionPreference = "Stop"

Write-Host "== Git basics =="
git rev-parse --is-inside-work-tree | Out-Null
Write-Host "branch:" (git branch --show-current)

Write-Host "`n== remotes =="
git remote -v

Write-Host "`n== local recent commits =="
git log --oneline -n 5

Write-Host "`n== remote heads (if origin exists) =="
$origin = git remote | Select-String -SimpleMatch "origin"
if ($origin) {
  git ls-remote --heads origin
} else {
  Write-Host "origin not configured"
}

Write-Host "`n== key artifact files =="
$files = @(
  "docs/event-crm-blueprint-ko.md",
  "docs/event-crm-implementation-playbook-ko.md",
  "ops/make/make-scenario-io-spec-ko.md",
  "ops/make/module-field-mapping.csv",
  "scripts/validate_ops_artifacts.py"
)
foreach ($f in $files) {
  if (Test-Path $f) { Write-Host "[OK] $f" } else { Write-Host "[MISS] $f" }
}

Write-Host "`n== validation =="
python scripts/validate_ops_artifacts.py
