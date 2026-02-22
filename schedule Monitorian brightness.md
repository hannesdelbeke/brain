---
views: 10
---
## goal
Auto dim monitor in the evening, and brighten in the [[morning]], to help with [[sleep]] and [[concentration|focus]].

## initial idea
use [[Windows task scheduler]] to schedule [[Monitorian]] 
- increase brightness in the morning, to help wake up and concentrate
- decrease brightness in the evening, to help with [[sleep]]

> [!NOTE]- Work in Progress
> this script creates both tasks:
> ```powershell
> $taskName = "AutoBrightnessMonitorian"
> $monitorianPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\Monitorian.exe"
> 
> # Define actions
> $actionMorning = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set 100"
> $actionEvening = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set 20"
> 
> # Define triggers
> $triggerMorning = New-ScheduledTaskTrigger -Daily -At 8:00AM
> $triggerEvening = New-ScheduledTaskTrigger -Daily -At 6:00PM
> 
> # Define settings (removing -DontStartIfOnBatteries)
> $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
> 
> # Register tasks
> Register-ScheduledTask -TaskName "${taskName}_Morning" -Action $actionMorning -Trigger $triggerMorning -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force
> Register-ScheduledTask -TaskName "${taskName}_Evening" -Action $actionEvening -Trigger $triggerEvening -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force
> 
> Write-Host "Scheduled tasks for Monitorian brightness adjustment have been set up successfully!"
> ```
> 
> 
> ## challenges
> 1. When starting the pc after the dim time, the schedule is missed causing dimming to not update.
> 2. The command didn't work in task scheduler.
>    I got it to work by setting the app to `C:\Users\USER\AppData\Local\Microsoft\WindowsApps\Monitorian.exe`, and the arguments to `/set 20` at 6pm, and `/set 100` at 8am
> 
> ## Todo 
> - [ ] handle starting the pc after dim time to adress challenge 1.
> - [ ] atm this makes script in temp folder which is bad. figure out a more long term location that doesn't get deleted, and doesn't require admin permissions to write to. and doesn't get lost during windows updates.
> ### Progress
> extended scripts WIP: Startup task that checks the current time and applies the correct brightness
> - This solves challenge #1.
> - But it introduces challenge #2:
> 
> ```powershell
> $taskName = "AutoBrightnessMonitorian"
> $monitorianPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\Monitorian.exe"
> 
> # Define actions
> $actionMorning = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set 100"
> $actionEvening = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set 20"
> 
> # Define triggers
> $triggerMorning = New-ScheduledTaskTrigger -Daily -At 8:00AM
> $triggerEvening = New-ScheduledTaskTrigger -Daily -At 6:00PM
> 
> # Define settings
> $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
> 
> # Register morning and evening tasks
> Register-ScheduledTask -TaskName "${taskName}_Morning" -Action $actionMorning -Trigger $triggerMorning -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force
> Register-ScheduledTask -TaskName "${taskName}_Evening" -Action $actionEvening -Trigger $triggerEvening -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force
> 
> # Define a startup action that checks the time and sets the correct brightness
> $startupScript = @"
> `$hour = (Get-Date).Hour
> if (`$hour -ge 8 -and `$hour -lt 18) {
>     Start-Process "$monitorianPath" -ArgumentList "/set 100"
> } else {
>     Start-Process "$monitorianPath" -ArgumentList "/set 20"
> }
> "@
> 
> $startupScriptPath = "$env:LOCALAPPDATA\Temp\SetBrightnessOnStartup.ps1"
> $startupScript | Out-File -Encoding UTF8 $startupScriptPath
> 
> # Create the startup task
> $actionStartup = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$startupScriptPath`""
> $triggerStartup = New-ScheduledTaskTrigger -AtStartup
> 
> Register-ScheduledTask -TaskName "${taskName}_Startup" -Action $actionStartup -Trigger $triggerStartup -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force
> 
> Write-Host "Scheduled tasks for Monitorian brightness adjustment have been set up successfully!"
> 
> ```

### log
- started with simple windows task to run on [[startup]]. worked but didn't work if you started your pc after the trigger hours.
- wrote new script with AI, it schedules the tasks on windows, but in between still seems to not work (tested 2026-02-22)

## final install script
⚠️ run as admin in [[powershell]], AFAIK shouldn't be needed, but I wasn't able to run this from Obsidian without admin.

my path is `C:\Program Files (x86)\Monitorian`, it might need changing
could be `$env:LOCALAPPDATA\Microsoft\WindowsApps\Monitorian.exe
```powershell
# ================================
# Auto Brightness for Monitorian
# ================================

# --- User‑configurable values ---
$brightLevel = 100
$dimLevel    = 20

$taskName = "AutoBrightnessMonitorian"
$monitorianPath = "C:\Program Files (x86)\Monitorian\Monitorian.exe"

# Persistent directory for helper script
$startupDir = "$env:LOCALAPPDATA\MonitorianAutoBrightness"
New-Item -ItemType Directory -Force -Path $startupDir | Out-Null

$startupScriptPath = "$startupDir\SetBrightnessOnStartup.ps1"

# -------------------------------
# Create helper script
# -------------------------------

$startupScript = @"
`$hour = (Get-Date).Hour

# Daytime: 08:00–17:59 → Bright
if (`$hour -ge 8 -and `$hour -lt 18) {
    Start-Process "$monitorianPath" -ArgumentList "/set $brightLevel"
}
# Evening/Night: 18:00–07:59 → Dim
else {
    Start-Process "$monitorianPath" -ArgumentList "/set $dimLevel"
}
"@

$startupScript | Out-File -Encoding UTF8 $startupScriptPath


# -------------------------------
# Define actions
# -------------------------------

$actionMorning = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set $brightLevel"
$actionEvening = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set $dimLevel"

$actionStartup = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$startupScriptPath`""


# -------------------------------
# Define triggers
# -------------------------------

$triggerMorning = New-ScheduledTaskTrigger -Daily -At 8:00AM
$triggerEvening = New-ScheduledTaskTrigger -Daily -At 6:00PM

# More reliable for Monitorian than AtStartup
$triggerStartup = New-ScheduledTaskTrigger -AtLogOn


# -------------------------------
# Define settings
# -------------------------------

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable


# -------------------------------
# Register tasks
# -------------------------------

Register-ScheduledTask `
    -TaskName "${taskName}_Morning" `
    -Action $actionMorning `
    -Trigger $triggerMorning `
    -Settings $settings `
    -User "$env:USERNAME" `
    -RunLevel Highest `
    -Force

Register-ScheduledTask `
    -TaskName "${taskName}_Evening" `
    -Action $actionEvening `
    -Trigger $triggerEvening `
    -Settings $settings `
    -User "$env:USERNAME" `
    -RunLevel Highest `
    -Force

Register-ScheduledTask `
    -TaskName "${taskName}_Startup" `
    -Action $actionStartup `
    -Trigger $triggerStartup `
    -Settings $settings `
    -User "$env:USERNAME" `
    -RunLevel Highest `
    -Force


Write-Host "Monitorian auto-brightness tasks installed successfully."
Write-Host "Helper script stored at: $startupScriptPath"

```

ading this at end should insta run it. but file not found.
and when i run ps1 file manually nothing happens, so maybe it's not working yet
```

# Run brightness logic immediately
powershell.exe -ExecutionPolicy Bypass -File "$startupScriptPath"
```
## uninstall

```powershell
# ================================
# Uninstall Auto Brightness Tasks
# ================================

$taskName = "AutoBrightnessMonitorian"

# Task names
$morningTask = "${taskName}_Morning"
$eveningTask = "${taskName}_Evening"
$startupTask = "${taskName}_Startup"

# Helper script directory
$startupDir = "$env:LOCALAPPDATA\MonitorianAutoBrightness"

Write-Host "Removing Monitorian auto-brightness tasks..."

# -------------------------------
# Remove scheduled tasks
# -------------------------------

$tasks = @($morningTask, $eveningTask, $startupTask)

foreach ($t in $tasks) {
    if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $t -Confirm:$false
        Write-Host "Removed task: $t"
    } else {
        Write-Host "Task not found (skipped): $t"
    }
}

# -------------------------------
# Remove helper script directory
# -------------------------------

if (Test-Path $startupDir) {
    Remove-Item -Recurse -Force $startupDir
    Write-Host "Removed helper script directory: $startupDir"
} else {
    Write-Host "Helper script directory not found (skipped): $startupDir"
}

Write-Host "Uninstall complete."
```

[[public/automate]]
relates to [[dark mode]] since both ease your eyes.