import os
import threading
import time
import customtkinter as ctk
import keyboard
import pyperclip
from audio_recorder import AudioRecorder
from transcriber import Transcriber

class JustSayApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JustSay")
        self.geometry("400x300")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.title_label = ctk.CTkLabel(self.main_frame, text="JustSay Dictation", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.status_label = ctk.CTkLabel(self.main_frame, text="Status: Idle", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=10)

        self.info_label = ctk.CTkLabel(self.main_frame, text="Hold Ctrl+Shift+Space to Dictate\nRelease to Transcribe & Type", font=ctk.CTkFont(size=12))
        self.info_label.pack(pady=10)

        # Initialize components
        self.recorder = AudioRecorder()
        self.transcriber = None
        self.is_recording = False
        
        self.status_label.configure(text="Status: Loading Model...")
        threading.Thread(target=self.load_model).start()

        # Setup Hotkey
        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()

    def load_model(self):
        self.transcriber = Transcriber(model_size="tiny")
        self.status_label.configure(text="Status: Idle. Ready to dictate.")

    def update_status(self, text):
        # Must update GUI from the main thread if possible, but ctk is sometimes forgiving.
        # Safer to use after:
        self.after(0, lambda: self.status_label.configure(text=f"Status: {text}"))

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
        
        # Stop recording in a separate thread so we don't block
        threading.Thread(target=self.process_audio).start()

    def process_audio(self):
        audio_file = self.recorder.stop_recording("temp_dictation.wav")
        if audio_file:
            self.update_status("Transcribing...")
            text = self.transcriber.transcribe(audio_file)
            
            if text:
                # Copy to clipboard and paste
                pyperclip.copy(text + " ")
                # Tiny delay to ensure clipboard is updated and hotkey is fully released
                time.sleep(0.1)
                keyboard.send("ctrl+v")
                self.update_status("Pasted!")
            else:
                self.update_status("No speech detected.")
                
            time.sleep(2)
            self.update_status("Idle. Ready to dictate.")

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = JustSayApp()
    app.mainloop()
