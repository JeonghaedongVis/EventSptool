Param(
  [string]$BranchName = "feat/event-crm-update"
)

$ErrorActionPreference = "Stop"

git checkout main
git pull origin main --ff-only
git checkout -b $BranchName

Write-Host "[OK] Created and switched to $BranchName"
Write-Host "Next: git add ."
Write-Host "      git commit -m 'feat: ...'"
Write-Host "      git push -u origin $BranchName"
