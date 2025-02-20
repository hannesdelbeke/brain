use [[task scheduler]] to schedule [[Monitorian]] 
- increase brightness in the morning, to help wake up and concentrate
- decrease brightness in the evening, to help with [[sleep]]

this script creates both tasks:
```powershell
$taskName = "AutoBrightnessMonitorian"
$monitorianPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\Monitorian.exe"

# Define actions
$actionMorning = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set 100"
$actionEvening = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set 20"

# Define triggers
$triggerMorning = New-ScheduledTaskTrigger -Daily -At 8:00AM
$triggerEvening = New-ScheduledTaskTrigger -Daily -At 6:00PM

# Define settings (removing -DontStartIfOnBatteries)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Register tasks
Register-ScheduledTask -TaskName "${taskName}_Morning" -Action $actionMorning -Trigger $triggerMorning -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force
Register-ScheduledTask -TaskName "${taskName}_Evening" -Action $actionEvening -Trigger $triggerEvening -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force

Write-Host "Scheduled tasks for Monitorian brightness adjustment have been set up successfully!"
```


got it to work by setting app to `C:\Users\USER\AppData\Local\Microsoft\WindowsApps\Monitorian.exe`
and arguments to `/set 20` at 6pm
and set it to 100 at 8am

## Todo 
advanced script to check time if pc is on after certain hour
atm this makes script in temp folder which is bad.

```powershell
$taskName = "AutoBrightnessMonitorian"
$monitorianPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\Monitorian.exe"

# Define actions
$actionMorning = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set 100"
$actionEvening = New-ScheduledTaskAction -Execute $monitorianPath -Argument "/set 20"

# Define triggers
$triggerMorning = New-ScheduledTaskTrigger -Daily -At 8:00AM
$triggerEvening = New-ScheduledTaskTrigger -Daily -At 6:00PM

# Define settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Register morning and evening tasks
Register-ScheduledTask -TaskName "${taskName}_Morning" -Action $actionMorning -Trigger $triggerMorning -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force
Register-ScheduledTask -TaskName "${taskName}_Evening" -Action $actionEvening -Trigger $triggerEvening -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force

# Define a startup action that checks the time and sets the correct brightness
$startupScript = @"
`$hour = (Get-Date).Hour
if (`$hour -ge 8 -and `$hour -lt 18) {
    Start-Process "$monitorianPath" -ArgumentList "/set 100"
} else {
    Start-Process "$monitorianPath" -ArgumentList "/set 20"
}
"@

$startupScriptPath = "$env:LOCALAPPDATA\Temp\SetBrightnessOnStartup.ps1"
$startupScript | Out-File -Encoding UTF8 $startupScriptPath

# Create the startup task
$actionStartup = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$startupScriptPath`""
$triggerStartup = New-ScheduledTaskTrigger -AtStartup

Register-ScheduledTask -TaskName "${taskName}_Startup" -Action $actionStartup -Trigger $triggerStartup -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force

Write-Host "Scheduled tasks for Monitorian brightness adjustment have been set up successfully!"

```


[[automate]]
relates to [[dark mode]] since both ease your eyes.