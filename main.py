import os
import threading
import time
import customtkinter as ctk
import keyboard
import pyperclip
from PIL import Image
import pystray
from pystray import MenuItem as item

from audio_recorder import AudioRecorder
from transcriber import Transcriber

class JustSayApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JustSay Dictation")
        self.geometry("400x300")
        
        # Withdraw window initially if we want to start in tray, or show it. Let's show it first.
        self.protocol('WM_DELETE_WINDOW', self.hide_window)

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.title_label = ctk.CTkLabel(self.main_frame, text="JustSay", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.status_label = ctk.CTkLabel(self.main_frame, text="Status: Loading Model...", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=10)

        self.info_label = ctk.CTkLabel(self.main_frame, text="Hold [Ctrl+Shift+Space] to dictate.\nRelease to auto-type.", font=ctk.CTkFont(size=13))
        self.info_label.pack(pady=10)

        self.settings_btn = ctk.CTkButton(self.main_frame, text="Hide to Tray", command=self.hide_window)
        self.settings_btn.pack(pady=20)

        # Initialize components
        self.recorder = AudioRecorder()
        self.transcriber = None
        self.is_recording = False
        
        threading.Thread(target=self.load_model, daemon=True).start()

        # Setup Hotkey
        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()

    def load_model(self):
        self.transcriber = Transcriber(model_size="tiny")
        self.update_status("Idle. Ready to dictate.")

    def update_status(self, text):
        try:
            self.after(0, lambda: self.status_label.configure(text=f"Status: {text}"))
        except:
            pass

    def hide_window(self):
        self.withdraw()
        image = Image.new('RGB', (64, 64), color = (73, 109, 137))
        menu = (item('Show', self.show_window), item('Quit', self.quit_window))
        self.icon = pystray.Icon("name", image, "JustSay", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon, item):
        self.icon.stop()
        self.after(0, self.deiconify)

    def quit_window(self, icon, item):
        self.icon.stop()
        self.after(0, self.destroy)
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
        if not self.transcriber:
            return
        self.is_recording = True
        self.update_status("Recording...")
        self.recorder.start_recording()

    def stop_dictation(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.update_status("Processing...")
        threading.Thread(target=self.process_audio, daemon=True).start()

    def process_audio(self):
        audio_file = self.recorder.stop_recording("temp_dictation.wav")
        if audio_file:
            self.update_status("Transcribing...")
            text = self.transcriber.transcribe(audio_file)
            if text:
                pyperclip.copy(text + " ")
                time.sleep(0.1)
                keyboard.send("ctrl+v")
                self.update_status("Pasted!")
            else:
                self.update_status("No speech detected.")
            time.sleep(2)
            self.update_status("Idle. Ready to dictate.")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = JustSayApp()
    app.mainloop()
