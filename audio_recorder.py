import pyaudio
import wave
import threading

class AudioRecorder:
    def __init__(self, chunk=1024, format=pyaudio.paInt16, channels=1, rate=16000, volume_callback=None):
        self.chunk = chunk
        self.format = format
        self.channels = channels
        self.rate = rate
        self.volume_callback = volume_callback
        self.p = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.stream = None
        self._record_thread = None

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.chunk)
        self._record_thread = threading.Thread(target=self._record)
        self._record_thread.start()

    def _record(self):
        import audioop
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
                if self.volume_callback:
                    rms = audioop.rms(data, 2)
                    self.volume_callback(rms)
            except Exception as e:
                print(f"Error recording audio: {e}")
                break

    def stop_recording(self, filename="temp_recording.wav"):
        self.is_recording = False
        if self._record_thread is not None:
            self._record_thread.join()
        
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        if not self.frames:
            return None

        # Save to file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        return filename

    def terminate(self):
        self.p.terminate()
