$ErrorActionPreference = "Stop"

if (-not (Test-Path "venv")) {
    Write-Host "Setting up Python virtual environment..."
    python -m venv venv
}
.\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..."
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

# We no longer use PyInstaller due to Smart App Control blocking unsigned executables.
# Instead, the installer packages the source and uses a native Python VBScript wrapper.

Write-Host "Compiling installer with Inno Setup..."
# Look for ISCC in typical locations
$isccPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)

$iscc = $null
foreach ($path in $isccPaths) {
    if (Test-Path $path) {
        $iscc = $path
        break
    }
}

if ($iscc) {
    & $iscc "installer.iss"
    Write-Host "Build complete! Installer is in the 'dist' folder."
} else {
    Write-Host "Inno Setup compiler (ISCC.exe) not found. Please compile installer.iss manually."
}

