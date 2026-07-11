import os
import threading
import time
import datetime
import multiprocessing
import webbrowser
import keyboard
import pyperclip
from PIL import Image
import pystray
from pystray import MenuItem as item

from audio_recorder import AudioRecorder
from transcriber import Transcriber
import database
from widget import run_widget_app

def run_server_process():
    import server
    server.run_server()

class JustSayApp:
    def __init__(self):
        database.init_db()
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(model_size="base")
        self.is_recording = False
        self.toggle_lock = threading.Lock()
        self.cmd_queue = multiprocessing.Queue()
        self.widget_process = multiprocessing.Process(target=run_widget_app, args=(self.cmd_queue,), daemon=True)
        self.server_process = multiprocessing.Process(target=run_server_process, daemon=True)

    def start(self):
        self.server_process.start()
        self.widget_process.start()

        # Register global hotkeys
        # Hotkey 1: Ctrl+Win held = push-to-talk (hold to record)
        # Hotkey 2: Ctrl+Win+Space = toggle record on/off
        keyboard.add_hotkey("ctrl+windows", self._ptt_start, suppress=False)
        keyboard.on_release_key("windows", self._ptt_stop_check)
        keyboard.add_hotkey("ctrl+windows+space", self._toggle_record, suppress=True)

        self.create_tray()

    # ── Push-to-Talk ──────────────────────────────────────────
    def _ptt_start(self):
        """Called when Ctrl+Win is pressed (push-to-talk start)."""
        # Only if Space is NOT pressed (to avoid conflict with toggle hotkey)
        if keyboard.is_pressed("space"):
            return
        if not self.is_recording:
            self.start_dictation()

    def _ptt_stop_check(self, e):
        """Called when Win key is released — stop PTT if recording."""
        if self.is_recording and not keyboard.is_pressed("ctrl+windows+space"):
            self.stop_dictation()

    # ── Toggle Record ─────────────────────────────────────────
    def _toggle_record(self):
        with self.toggle_lock:
            if self.is_recording:
                self.stop_dictation()
            else:
                self.start_dictation()

    # ── Core recording ────────────────────────────────────────
    def start_dictation(self):
        self.is_recording = True
        self.cmd_queue.put("START")
        self.recorder.start_recording()

    def stop_dictation(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.cmd_queue.put("STOP")
        threading.Thread(target=self.process_audio, daemon=True).start()

    def process_audio(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
        os.makedirs(audio_dir, exist_ok=True)
        audio_file_path = os.path.join(audio_dir, f"dictation_{timestamp}.wav")

        audio_file = self.recorder.stop_recording(audio_file_path)
        if not audio_file:
            return

        settings = database.get_user_settings("localuser@localhost")
        style = settings["speaking_style"] if settings else "Casual"
        dictionary_words = database.get_dictionary()
        dict_str = ", ".join(dictionary_words)
        user_prompt = database.get_active_prompt()
        prompt = f"Style: {style}. {user_prompt} Key terms: {dict_str}".strip()

        text = self.transcriber.transcribe(audio_file, initial_prompt=prompt)
        if text:
            database.save_history(audio_file, text)
            pyperclip.copy(text + " ")
            time.sleep(0.1)
            keyboard.send("ctrl+v")
            self.cmd_queue.put("PASTED")

    # ── Tray ──────────────────────────────────────────────────
    def create_tray(self):
        image = Image.new('RGB', (64, 64), color=(124, 92, 252))
        menu = (
            item('Open Dashboard', self.open_dashboard),
            item('Quit JustSay', self.quit_app)
        )
        self.icon = pystray.Icon("JustSay", image, "JustSay — Voice AI", menu)
        self.icon.run()

    def open_dashboard(self, icon, item):
        webbrowser.open("http://localhost:2000")

    def quit_app(self, icon, item):
        self.cmd_queue.put("QUIT")
        self.icon.stop()
        os._exit(0)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = JustSayApp()
    app.start()
