Param(
  [string]$RemoteUrl = ""
)

$ErrorActionPreference = "Stop"

if ($RemoteUrl -ne "") {
  $originExists = git remote | Select-String -SimpleMatch "origin"
  if ($originExists) {
    git remote set-url origin $RemoteUrl
  }
  else {
    git remote add origin $RemoteUrl
  }
}

$originConfigured = git remote | Select-String -SimpleMatch "origin"
if (-not $originConfigured) {
  Write-Error "origin remote is not configured. Pass -RemoteUrl first."
}

git fetch origin --prune

git checkout -B main origin/main
git pull --ff-only origin main

Write-Host "Sync complete. Current branch:" (git branch --show-current)
git log --oneline -n 3
