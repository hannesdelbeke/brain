---
date: 2026-08-24
tags:
  - technical
  - obsidian
  - performance
  - windows
---
When indexing or searching large vaults (5k+ notes), Windows Defender real-time scanning (`MsMpEng.exe`) intercepts file I/O calls, causing search latency and UI lag.

Reading the exclusion list requires Administrator privileges (non-admin returns `N/A: Must be an administrator to view exclusions`).

### Verify Exclusions (PowerShell Admin)

```powershell
$vaultPath = "C:\repos\pkm"
$pref = Get-MpPreference

[PSCustomObject]@{
    VaultPath        = $vaultPath
    FolderExcluded   = ($pref.ExclusionPath -contains $vaultPath)
    ObsidianProcess  = ($pref.ExclusionProcess -contains "Obsidian.exe")
    AllExcludedPaths = ($pref.ExclusionPath -join ", ")
} | Format-List
```

### Quick Verification Popup (Elevated UAC)

```powershell
Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile", "-Command", "Write-Host '=== Defender Exclusions ===' -ForegroundColor Cyan; (Get-MpPreference).ExclusionPath; (Get-MpPreference).ExclusionProcess; pause"
```

### Add Exclusions (PowerShell Admin)

```powershell
# Exclude vault folder
Add-MpPreference -ExclusionPath "C:\repos\pkm"

# Exclude Obsidian process
Add-MpPreference -ExclusionProcess "Obsidian.exe"
```

## References
- [[Obsidian faster startup]]
- [[2026-08-12 Obsidian plugin startup optimization]]
- [[2026-07-22 Obsidian slow]]
- [[Obsidian plugins in use]]
