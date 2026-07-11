import os
import threading
import time
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

# For multiprocessing, we might use a Queue to send commands to the widget
from widget import run_widget_app

def run_server_process():
    import server
    server.run_server()

class JustSayApp:
    def __init__(self):
        database.init_db()
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(model_size="base") # Upgraded to base for better formatting
        self.is_recording = False
        
        self.cmd_queue = multiprocessing.Queue()
        
        self.widget_process = multiprocessing.Process(target=run_widget_app, args=(self.cmd_queue,), daemon=True)
        self.server_process = multiprocessing.Process(target=run_server_process, daemon=True)

    def start(self):
        self.server_process.start()
        self.widget_process.start()

        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()

        self.create_tray()

    def create_tray(self):
        image = Image.new('RGB', (64, 64), color=(187, 134, 252))
        menu = (
            item('Dashboard (localhost:2000)', self.open_dashboard),
            item('Quit', self.quit_app)
        )
        self.icon = pystray.Icon("JustSay", image, "JustSay", menu)
        self.icon.run()

    def open_dashboard(self, icon, item):
        webbrowser.open("http://localhost:2000")

    def quit_app(self, icon, item):
        self.cmd_queue.put("QUIT")
        self.icon.stop()
        os._exit(0)

    def hotkey_listener(self):
        hotkey = "ctrl+shift+space"
        was_pressed = False
        while True:
            is_pressed = keyboard.is_pressed(hotkey)
            if is_pressed and not was_pressed:
                was_pressed = True
                self.start_dictation()
            elif not is_pressed and was_pressed:
                was_pressed = False
                self.stop_dictation()
            time.sleep(0.05)

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
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
        os.makedirs(audio_dir, exist_ok=True)
        audio_file_path = os.path.join(audio_dir, f"dictation_{timestamp}.wav")
        
        audio_file = self.recorder.stop_recording(audio_file_path)
        if audio_file:
            # Build the mega prompt based on style, active prompt, and dictionary
            # For a local-only setup, we get user style from the default user
            settings = database.get_user_settings("localuser@localhost")
            style = settings["speaking_style"] if settings else "Casual"
            
            dictionary_words = database.get_dictionary()
            dict_str = ", ".join(dictionary_words)
            
            user_prompt = database.get_active_prompt()
            
            # initial_prompt max tokens is 224 for whisper. Keep it concise.
            prompt = f"Style: {style}. {user_prompt} Keywords: {dict_str}"
            
            text = self.transcriber.transcribe(audio_file, initial_prompt=prompt)
            if text:
                database.save_history(audio_file, text)
                pyperclip.copy(text + " ")
                time.sleep(0.1)
                keyboard.send("ctrl+v")
                
                # Signal the widget to show the Undo popup
                self.cmd_queue.put("PASTED")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = JustSayApp()
    app.start()
