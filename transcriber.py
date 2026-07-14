from faster_whisper import WhisperModel
import os

class Transcriber:
    def __init__(self, model_size="tiny", compute_type="int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        print(f"Loading Whisper model '{model_size}'...")
        self.model = WhisperModel(self.model_size, device="auto", compute_type=self.compute_type)
        print("Model loaded.")

    def transcribe(self, audio_path, initial_prompt=""):
        if not os.path.exists(audio_path):
            return ""
        
        # Transcribe audio using initial_prompt for context
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5, 
            initial_prompt=initial_prompt if initial_prompt else None,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        text = "".join([segment.text for segment in segments]).strip()
        
        # Filter out common hallucination phrases caused by silence
        hallucination_phrases = ["Transcribe accurately", "Key terms.", "maintaining proper capitalization"]
        if any(phrase in text for phrase in hallucination_phrases) and len(text) < 300:
            return ""
            
        return text
