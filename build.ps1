$ErrorActionPreference = "Stop"

Write-Host "Setting up Python virtual environment..."
python -m venv venv
.\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..."
# Bypassing SSL issues by trusting the hosts
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

Write-Host "Building executable with PyInstaller..."
# We use --windowed to hide the console window and --onefile to produce a single .exe
pip install pyinstaller --trusted-host pypi.org --trusted-host files.pythonhosted.org
pyinstaller --onefile --windowed --name "JustSay" --add-data "audio_recorder.py;." --add-data "transcriber.py;." main.py

Write-Host "Build complete! You can find JustSay.exe in the 'dist' folder."
