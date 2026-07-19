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
        self.recorder = AudioRecorder(volume_callback=self._on_volume)
        self.transcriber = Transcriber(model_size="base")
        self.is_recording = False
        self.toggle_lock = threading.Lock()
        self.cmd_queue = multiprocessing.Queue()
        self.widget_process = multiprocessing.Process(target=run_widget_app, args=(self.cmd_queue,), daemon=True)
        self.server_process = multiprocessing.Process(target=run_server_process, daemon=True)
    def _on_volume(self, rms):
        if self.is_recording:
            self.cmd_queue.put(f"VOL:{rms}")

    def start(self):
        self.server_process.start()
        self.widget_process.start()

        # Start the background hotkey listener thread
        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()

        self.create_tray()

    def hotkey_listener(self):
        ptt_was_pressed = False
        toggle_was_pressed = False
        
        while True:
            # Check db for latest user settings
            settings = database.get_user_settings("localuser@localhost")
            if settings:
                ptt_hotkey = settings.get("hotkey_ptt", "ctrl+windows")
                toggle_hotkey = settings.get("hotkey_toggle", "ctrl+windows+space")
            else:
                ptt_hotkey = "ctrl+windows"
                toggle_hotkey = "ctrl+windows+space"

            def is_combo_pressed(combo):
                if not combo:
                    return False
                keys = combo.lower().replace(" ", "").split("+")
                try:
                    # Translate common aliases
                    translated = []
                    for k in keys:
                        if k in ("windows", "win"):
                            translated.append("left windows") # keyboard library handles this well
                        elif k in ("control", "ctrl"):
                            translated.append("ctrl")
                        else:
                            translated.append(k)
                    return all(keyboard.is_pressed(k) for k in translated)
                except:
                    return False

            toggle_pressed = is_combo_pressed(toggle_hotkey)
            ptt_pressed = is_combo_pressed(ptt_hotkey)

            # Resolve toggle click
            if toggle_pressed:
                if not toggle_was_pressed:
                    toggle_was_pressed = True
                    self._toggle_record()
            else:
                toggle_was_pressed = False

            # Resolve PTT hold
            if ptt_pressed and not toggle_pressed:
                if not self.is_recording and not ptt_was_pressed:
                    ptt_was_pressed = True
                    self.start_dictation()
            else:
                if ptt_was_pressed:
                    ptt_was_pressed = False
                    if self.is_recording:
                        self.stop_dictation()

            time.sleep(0.05)

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
        audio_dir = database.AUDIO_DIR
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
            database.save_history(text)
            pyperclip.copy(text + " ")
            
            # Release modifiers to prevent Ctrl+V collision
            for mod in ["ctrl", "shift", "alt", "windows"]:
                try: keyboard.release(mod)
                except: pass
                
            time.sleep(0.1)
            keyboard.send("ctrl+v")
            self.cmd_queue.put("PASTED")
            
        # Delete audio file to respect privacy and save storage
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception:
            pass

    # ── Tray ──────────────────────────────────────────────────
    def create_tray(self):
        from PIL import ImageDraw
        image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((4, 4, 60, 60), fill=(41, 151, 255, 255))
        
        menu = (
            item('Open Dashboard', self.open_dashboard),
            item('Quit JustSay', self.quit_app)
        )
        self.icon = pystray.Icon("JustSay", image, "JustSay — Voice AI", menu)
        self.icon.run()

    def open_dashboard(self, icon, item):
        import multiprocessing
        from webview_app import run_webview_app
        p = multiprocessing.Process(target=run_webview_app, daemon=True)
        p.start()

    def quit_app(self, icon, item):
        self.cmd_queue.put("QUIT")
        if self.widget_process.is_alive():
            self.widget_process.terminate()
        if self.server_process.is_alive():
            self.server_process.terminate()
        self.icon.stop()
        import sys
        sys.exit(0)

import socket
import sys

def enforce_single_instance():
    try:
        global _lock_socket
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _lock_socket.bind(("127.0.0.1", 49191))
    except OSError:
        print("Another instance of JustSay is already running. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    enforce_single_instance()
    app = JustSayApp()
    app.start()
