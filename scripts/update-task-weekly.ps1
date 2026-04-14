# update-task-weekly.ps1
# Re-registers the LinkedIn Comment Bot as a Windows Scheduled Task.
# Run this script once (as Administrator) to set up or update the task.
# The task will launch main.py daily at 1:55 PM so it's ready for the 2-5 PM window.

$taskName    = "LinkedInCommentBot"
$botDir      = "C:\Users\richm\.claude\linkedin-comment-bot"
$pythonExe   = "python"   # Use full path if python is not on PATH, e.g. "C:\Python311\python.exe"
$scriptPath  = "$botDir\main.py"
$logFile     = "$botDir\task_scheduler.log"

# Remove old task if it exists
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing task: $taskName"
}

# Action: run python main.py, log stdout+stderr to file
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$pythonExe `"$scriptPath`" >> `"$logFile`" 2>&1`"" `
    -WorkingDirectory $botDir

# Trigger: daily at 1:55 PM (gives 5 min warm-up before the 2 PM window)
$trigger = New-ScheduledTaskTrigger -Daily -At "13:55"

# Settings: allow running when on battery, don't stop if on AC, restart on failure
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
    -RestartCount 1 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Principal: run as current user, only when logged on (needed for visible browser)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "LinkedIn Comment Reply Bot — checks Rich's posts 2-5 PM daily and auto-replies to comments."

Write-Host ""
Write-Host "Task registered: $taskName"
Write-Host "Runs daily at 1:55 PM"
Write-Host "Log: $logFile"
Write-Host ""
Write-Host "To run immediately for testing:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "To remove the task:"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
