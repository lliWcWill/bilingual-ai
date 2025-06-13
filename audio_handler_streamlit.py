"""
Streamlit Cloud-compatible audio recording using streamlit-audio-recorder
This replaces sounddevice which requires system audio libraries not available on Streamlit Cloud
"""
import tempfile
import os
from audio_recorder_streamlit import audio_recorder
import streamlit as st

class StreamlitAudioRecorder:
    def __init__(self):
        self.audio_file = None
        self.is_recording = False
    
    def start_recording(self):
        """Start recording - handled by the audio_recorder component"""
        self.is_recording = True
        return True
    
    def stop_recording(self):
        """Stop recording and return the audio file path"""
        self.is_recording = False
        
        # Use the audio recorder component
        audio_bytes = audio_recorder(
            text="🎤 Click to record",
            recording_color="#ff4444",
            neutral_color="#00d4ff",
            icon_name="microphone",
            icon_size="3x",
            pause_threshold=2.0,
            sample_rate=16000,
            key="audio_recorder"
        )
        
        if audio_bytes:
            # Save the recorded audio to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                self.audio_file = temp_file.name
                return temp_file.name
        
        return None
    
    def get_audio_file(self):
        """Return the current audio file path"""
        return self.audio_file