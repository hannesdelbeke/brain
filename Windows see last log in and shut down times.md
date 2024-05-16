
```powershell
# Get user login time
$LoginTime = Get-WinEvent -FilterHashtable @{Logname='Security';ID=4624} -MaxEvents 1 | Select-Object -ExpandProperty TimeCreated

# Get the 5 most recent shutdown times
$ShutdownTimes = Get-WinEvent -FilterHashtable @{Logname='System';ID=1074} -MaxEvents 5 | Select-Object -ExpandProperty TimeCreated

Write-Host "User logged in at (requires run as admin): $LoginTime"
Write-Host "Last 5 shutdowns:"
$ShutdownTimes | ForEach-Object { Write-Host $_ }

pause
```

and a cmd launcher for the [[powershell]] script, needs to be run as admin
```batch
echo off
:: cd current folder
cd .
powershell.exe -ExecutionPolicy Bypass -File "%~dp0login_shutdown_info.ps1"
pause
```

[[Windows]]