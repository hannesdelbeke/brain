uninstall preinstalled apps on win 11 pc from scan
ensure winget is installed, then copy paste this in an elevated command prompt

```batch
REM TODO check if winget installed, otherwise open it
start ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1

winget uninstall Burnintest_is1
winget uninstall CrystalDewWorld.CrystalDiskMark
winget uninstall FinalWire.AIDA64.Extreme
winget uninstall REALiX.HWiNFO
winget uninstall "PerformanceTest 10_is1"

REM 3DMark
winget uninstall {286cb379-a9b3-4fc6-a284-44cb1129a316}

REM Geeks3D FurMark 1.29.0.0
winget uninstall {2397CAD4-2263-4CD0-96BE-E43A980B9C9A}_is1

REM Futuremark SystemInfo
winget uninstall {63C33A87-484C-4D23-BAA4-5658DD908D8E}

winget uninstall Microsoft.BingNews_8wekyb3d8bbwe
winget uninstall Microsoft.BingWeather_8wekyb3d8bbwe
winget uninstall Microsoft.MicrosoftSolitaireCollection_8wekyb3d8bbwe
winget uninstall Microsoft.ZuneMusic_8wekyb3d8bbwe
winget uninstall Microsoft.WindowsFeedbackHub_8wekyb3d8bbwe
winget uninstall Microsoft.GetHelp_8wekyb3d8bbwe
winget uninstall MicrosoftTeams_8wekyb3d8bbwe
winget uninstall Microsoft.ZuneVideo_8wekyb3d8bbwe

echo FINISHED
```

#winget