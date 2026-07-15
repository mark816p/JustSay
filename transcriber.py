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
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        text = "".join([segment.text for segment in segments]).strip()
        
        # Aggressive filter for hallucinations when there is mostly silence
        text_lower = text.lower()
        if "transcribe accurately" in text_lower or "maintaining proper capitalization" in text_lower or "key terms." in text_lower:
            return ""
        
        # If the output just regurgitates the initial prompt or is too short
        if initial_prompt and text_lower in initial_prompt.lower():
            return ""
            
        return text
