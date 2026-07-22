import os
import wave
import pytest
from unittest.mock import MagicMock, patch
pytest.importorskip("pyaudio")
from audio_recorder import AudioRecorder

def test_audio_recorder_init():
    recorder = AudioRecorder(chunk=512, rate=16000)
    assert recorder.chunk == 512
    assert recorder.rate == 16000
    assert recorder.is_recording is False

@patch('audio_recorder.pyaudio.PyAudio')
def test_audio_recorder_save(mock_pyaudio, tmp_path):
    out_file = str(tmp_path / "test.wav")
    recorder = AudioRecorder()
    recorder.frames = [b'\x00\x00' * 512]
    
    saved_path = recorder.stop_recording(out_file)
    assert saved_path == out_file
    assert os.path.exists(out_file)
