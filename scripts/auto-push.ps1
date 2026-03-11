# Auto-push script for claude-vscode-assistant
# Scheduled daily at 5:00 AM EST via Windows Task Scheduler

$repoPath = "C:\Users\richm\.claude"
$logFile = "$repoPath\scripts\auto-push.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Set-Location $repoPath

# Stage all changes
git add -A

# Check if there is anything to commit
$status = git status --porcelain
if ($status) {
    git commit -m "auto: daily sync $timestamp"
    git push origin master
    Add-Content $logFile "[$timestamp] SUCCESS: Changes pushed to origin/master"
} else {
    Add-Content $logFile "[$timestamp] SKIP: No changes to push"
}
