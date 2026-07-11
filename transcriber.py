from faster_whisper import WhisperModel
import os

class Transcriber:
    def __init__(self, model_size="tiny", compute_type="int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        print(f"Loading Whisper model '{model_size}'...")
        # device="auto" automatically selects GPU if available, else CPU
        self.model = WhisperModel(self.model_size, device="auto", compute_type=self.compute_type)
        print("Model loaded.")

    def transcribe(self, audio_path):
        if not os.path.exists(audio_path):
            return ""
        
        # Transcribe audio
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        text = "".join([segment.text for segment in segments])
        return text.strip()
