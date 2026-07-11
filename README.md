# JustSay — Local Voice Dictation OS for Windows

JustSay is an ultra-fast, local-first, privacy-respecting dictation system for Windows. Built on top of `faster-whisper` and designed with a premium, custom dashboard, JustSay allows you to type with your voice anywhere on your system using high-efficiency offline neural models.

---

## 🌟 Key Features

*   **Universal Offline Dictation:** Instantly transcribe your voice in any active text box across Windows using a local Whisper model.
*   **Push-to-Talk & Toggles:** Use system-wide keyboard triggers to record exactly when you want.
*   **Real-time Waveform Overlay:** A beautiful floating UI pill sits above your taskbar during recording to show live audio capture.
*   **Undo & Quick Correction (Local Vocabulary):** Dictated something wrong? Click the 4-second "Undo & Correct" floating pill to undo the text and teach JustSay the correct spelling.
*   **AI Instructions / Formatting Rules:** Inject custom system prompts to guide formatting, capitalization, or markdown injection.
*   **Speech Insights & Telemetry:** Review local statistics on words dictated, session history, and speaking flow styles.
*   **100% On-Device Isolation:** Audio captures, transcripts, settings, and database entries are stored entirely on your device. Absolutely no telemetry leaves your machine.
*   **Premium Web Dashboard:** Configure settings, manage active rules, browse history, play audio files, and toggle Dark/Light themes at `http://localhost:2000`.

---

## 🎹 Global Shortcuts

| Shortcut Key | Function | Description |
| :--- | :--- | :--- |
| **`Ctrl` + `Win` (Hold)** | **Push-to-Talk** | Hold to record audio, release to instantly paste text. |
| **`Ctrl` + `Win` + `Space`** | **Toggle Record** | Tap once to start, tap again to finish. Ideal for hands-free dictation. |
| **`Click Overlay Pill`** | **Undo & Correct** | Pops up for 4 seconds after dictating. Click to undo and train the model. |

---

## 🛠️ Requirements & Dependencies

JustSay uses a modular, local multi-processing system:
*   **Backend engine:** `faster-whisper` (utilizing the Whisper `base` model).
*   **Database:** SQLite (local persistent settings, rules, dictionary, and history).
*   **Control Center / Dashboard:** Flask web server running at `http://localhost:2000` with full dark/light modes.
*   **Overlay Widget:** PyQt6 frameless transparent pill.
*   **System Listeners:** `keyboard`, `pyperclip`, and `pyaudio` for desktop hooks.

To run/compile manually, install the requirements:
```bash
pip install -r requirements.txt
```

---

## 🚀 Building & Installation

### Option 1: Automatic Installer
JustSay comes with a PowerShell script to set up, install, and add standard shortcuts to your Start Menu and Desktop:
1. Open PowerShell as Administrator.
2. Run the installer:
   ```powershell
   .\Install-JustSay.ps1
   ```

### Option 2: Build Executable Manually
To build a standalone executable that runs inside the system tray:
1. Run the build script:
   ```powershell
   .\build.ps1
   ```
2. The built binary can be found in `dist/JustSay.exe`.

---

## 🔒 Privacy & Local Sovereignty

Unlike cloud dictation APIs, JustSay runs completely locally.
*   No transcription data is transmitted to the cloud.
*   History recordings are saved directly into the `history_audio/` subdirectory.
*   Settings, statistics, and instructions are kept locally inside `justsay_data.db`.
*   Google Login is only utilized for local profiling/saving of preferences, and does not upload your telemetry.
