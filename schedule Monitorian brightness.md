schedule [[Monitorian]] to auto set brightness at certain times
## Windows
- Save this powershell script, and run it on [[Windows 10]].
- Run with bypass executionpolicy to avoid the script not running:
  `powershell -ExecutionPolicy Bypass -File "C:\Users\H\Desktop\sunset.ps1"`

```powershell
# Variables for location (latitude and longitude of Manchester)
$latitude = "53.4839"
$longitude = "-2.2446"

# API URL for Sunrise-Sunset
$url = "https://api.sunrise-sunset.org/json?lat=$latitude&lng=$longitude&formatted=0"

# Make the API call
$response = Invoke-RestMethod -Uri $url -Method Get
$sunsetUTC = $response.results.sunset

# Convert sunset UTC time to local time
$sunsetLocal = [DateTime]::Parse($sunsetUTC).ToLocalTime()

# Extract hours and minutes for Task Scheduler
$sunsetHour = $sunsetLocal.Hour
$sunsetMinute = $sunsetLocal.Minute

# Task 1: Sunset Task
$taskNameSunset = "Adjust Monitorian Brightness at Sunset"
$brightnessCommandSunset = 'Start-Process "Monitorian.exe" -ArgumentList "/set 20"'

$sunsetTaskExists = Get-ScheduledTask -TaskName $taskNameSunset -ErrorAction SilentlyContinue
if ($sunsetTaskExists) {
    Write-Output "The task '$taskNameSunset' already exists."
} else {
    # Create sunset task
    $actionSunset = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command $brightnessCommandSunset"
    $triggerSunset = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($sunsetHour).AddMinutes($sunsetMinute))
    $settingsSunset = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
    $taskSunset = New-ScheduledTask -Action $actionSunset -Trigger $triggerSunset -Settings $settingsSunset

    Register-ScheduledTask -TaskName $taskNameSunset -InputObject $taskSunset -Force
    Write-Output "Task '$taskNameSunset' created successfully."
}

# Task 2: Sunrise Task
$taskNameSunrise = "Adjust Monitorian Brightness at Sunrise"
$brightnessCommandSunrise = 'Start-Process "Monitorian.exe" -ArgumentList "/set 70"'
$sunriseHour = 7
$sunriseMinute = 0

$sunriseTaskExists = Get-ScheduledTask -TaskName $taskNameSunrise -ErrorAction SilentlyContinue
if ($sunriseTaskExists) {
    Write-Output "The task '$taskNameSunrise' already exists."
} else {
    # Create sunrise task
    $actionSunrise = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command $brightnessCommandSunrise"
    $triggerSunrise = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($sunriseHour).AddMinutes($sunriseMinute))
    $settingsSunrise = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
    $taskSunrise = New-ScheduledTask -Action $actionSunrise -Trigger $triggerSunrise -Settings $settingsSunrise

    Register-ScheduledTask -TaskName $taskNameSunrise -InputObject $taskSunrise -Force
    Write-Output "Task '$taskNameSunrise' created successfully."
}
```

[[automate]]