
powershell code to [[Python packages editable install|editable install]] all python packages in my repos folder

to `C:/Users/%username%/Documents/Maya/scripts` without dependencies
make sure to expand username, and don't assume the scripts folder exists. not sure if that matters for a pip install.

```powershell
$reposPath = "D:\repos"
$targetPath = "C:\Users\$env:USERNAME\Documents\Maya\scripts"
$excludeKeywords = @("blender", "unity")

# Ensure the target directory exists
if (!(Test-Path -Path $targetPath)) {
    New-Item -ItemType Directory -Path $targetPath | Out-Null
}

Write-Host "Looking for Python projects in $reposPath..."

# Find all Python projects (folders with pyproject.toml)
$projects = Get-ChildItem -Path $reposPath -Directory
Write-Host "Found directories: $($projects | ForEach-Object { $_.FullName })"

$projects = $projects | Where-Object {
    $pyprojectPath = Join-Path $_.FullName "pyproject.toml"
    $projectName = $_.Name
    
    # Check if project should be skipped
    if ($excludeKeywords | Where-Object { $projectName -match $_ }) {
        Write-Host "Skipping: $projectName (matches exclude keywords)"
        return $false
    }
    
    Write-Host "Checking: $pyprojectPath"
    Test-Path $pyprojectPath
}

Write-Host "Filtered projects with pyproject.toml: $($projects | ForEach-Object { $_.FullName })"

foreach ($project in $projects) {
    Write-Host "Installing $($project.FullName) in editable mode..."
    pip install -e "$($project.FullName)" --no-deps --target "$targetPath"
}
```

example of installing a single package
```powershell
$targetPath = "C:\Users\H\Documents\maya\scripts\site-packages"
pip install -e "D:/repos/plugget" --no-deps --target "$targetPath"
```
[[support Maya site packages in documents folder]]
[[Python packages editable install]]

