$ErrorActionPreference = "Stop"

$AppName = "JustSay"
$ExeName = "JustSay.exe"
$SourcePath = Join-Path $PSScriptRoot "dist\$ExeName"
$InstallDir = Join-Path $env:ProgramFiles $AppName
$DestPath = Join-Path $InstallDir $ExeName

# Check if run as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run this installer as Administrator!" -ForegroundColor Red
    Write-Host "Right-click the script and select 'Run with PowerShell' or run in an Admin prompt."
    Pause
    Exit
}

if (-not (Test-Path $SourcePath)) {
    Write-Host "Executable not found at $SourcePath. Please run build.ps1 first!" -ForegroundColor Red
    Pause
    Exit
}

Write-Host "Installing $AppName..."

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

Write-Host "Copying files to $InstallDir..."
Copy-Item -Path $SourcePath -Destination $DestPath -Force

Write-Host "Creating Desktop Shortcut..."
$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\$AppName.lnk")
$Shortcut.TargetPath = $DestPath
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Save()

Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "You can now launch JustSay from your Desktop."
Pause
