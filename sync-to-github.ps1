# Sync .claude config to GitHub
# Run this script whenever you want to push updates

Set-Location "C:\Users\richm\.claude"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$status = git status --porcelain

if (-not $status) {
    Write-Host "Nothing to sync - already up to date." -ForegroundColor Green
    exit 0
}

git add .
git commit -m "sync: $timestamp"
git push

Write-Host "Synced to GitHub!" -ForegroundColor Green
