# JustSay - Local Dictation App for Windows

JustSay is a sleek, locally-run dictation application designed for Windows, inspired by Wispr Flow. It uses powerful offline AI models (via faster-whisper) to convert your speech into text instantly and types it directly into your active window.

## Features

- **Offline & Private**: Powered by `faster-whisper`. Audio is processed entirely on your machine.
- **Global Hotkey**: Hold `Ctrl+Shift+Space` from anywhere to start dictating.
- **Auto-Type**: Release the hotkey, and JustSay instantly types your transcribed text into your currently focused application.
- **System Tray Integration**: Unobtrusive. Minimizes to the system tray so it stays out of your way.
- **Modern UI**: Clean, dark-mode interface built with CustomTkinter.

## Installation

### Option 1: Use the Installer (Recommended)
Download the `JustSay.exe` from the latest release (or build it yourself) and run it. No installation is necessary—it's a standalone portable app!

### Option 2: Run from Source
Make sure you have Python 3.9+ installed.

1. Clone this repository:
   ```bash
   git clone https://github.com/mark816p/JustSay.git
   cd JustSay
   ```

2. Create a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Run the app:
   ```powershell
   python main.py
   ```

## Usage

1. Launch JustSay.
2. Wait for the status to say "Idle. Ready to dictate." (It downloads a tiny Whisper model on first run).
3. Select the text field in any application where you want to type.
4. **Hold down `Ctrl + Shift + Space`** and speak.
5. **Release the keys**. The app will transcribe your speech and instantly paste it!
6. Click "Hide to Tray" to keep it running in the background.

## Building the Executable

Run the provided PowerShell script to build your own standalone `.exe`:

```powershell
.\build.ps1
```

The compiled application will be located in the `dist/` folder.
