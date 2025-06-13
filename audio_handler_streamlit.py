import sounddevice as sd
import wavio
import numpy as np
import tempfile
import time
from config import LOGGERS, AUDIO_RATE, AUDIO_CHANNELS, AUDIO_SAMPLE_WIDTH

logger = LOGGERS['audio']

class StreamlitAudioRecorder:
    """Streamlit-optimized audio recorder with comprehensive logging"""
    
    def __init__(self):
        logger.info("Initializing StreamlitAudioRecorder")
        self.audio_frames = []
        self.is_recording = False
        self.stream = None
        self.sample_rate = AUDIO_RATE
        self.channels = AUDIO_CHANNELS
        self.sample_width = AUDIO_SAMPLE_WIDTH
        logger.debug(f"Audio config: rate={self.sample_rate}, channels={self.channels}, sample_width={self.sample_width}")

    def _record_callback(self, indata, frames, time, status):
        """Callback function for audio recording"""
        if status:
            logger.warning(f"Audio input status: {status}")
        
        if self.is_recording:
            self.audio_frames.append(indata.copy())
            # Only log occasionally to avoid spam
            if len(self.audio_frames) % 50 == 0:  # Log every 50th frame
                logger.debug(f"Recording... {len(self.audio_frames)} frames captured")

    def start_recording(self):
        """Start non-blocking audio recording"""
        logger.info("Starting audio recording")
        try:
            self.audio_frames = []
            self.is_recording = True
            
            # Create and start audio stream
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._record_callback,
                dtype=np.float32
            )
            self.stream.start()
            logger.info("Audio stream started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self):
        """Stop recording and return audio file path"""
        logger.info("Stopping audio recording")
        
        if not self.is_recording:
            logger.warning("Attempted to stop recording but not currently recording")
            return None
            
        try:
            # Stop the stream
            if self.stream:
                self.stream.stop()
                self.stream.close()
                logger.debug("Audio stream stopped and closed")
            
            self.is_recording = False
            
            # Check if we have audio data
            if not self.audio_frames:
                logger.warning("No audio frames recorded")
                return None
            
            # Save audio file
            audio_file = self._save_audio()
            logger.info(f"Recording stopped successfully, saved to: {audio_file}")
            return audio_file
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return None

    def _save_audio(self):
        """Save recorded audio frames to a temporary file"""
        logger.debug(f"Saving {len(self.audio_frames)} audio frames")
        
        try:
            # Concatenate all audio frames
            recording = np.concatenate(self.audio_frames, axis=0)
            logger.debug(f"Concatenated audio shape: {recording.shape}")
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_path = temp_file.name
            temp_file.close()
            
            # Save to WAV file
            wavio.write(temp_path, recording, self.sample_rate, sampwidth=self.sample_width)
            
            # Get file size for logging
            import os
            file_size = os.path.getsize(temp_path)
            duration = len(recording) / self.sample_rate
            
            logger.info(f"Audio saved: {temp_path}")
            logger.debug(f"File size: {file_size} bytes, Duration: {duration:.2f}s")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            return None

    def is_recording_active(self):
        """Check if recording is currently active"""
        return self.is_recording

    def get_recording_duration(self):
        """Get current recording duration in seconds"""
        if not self.is_recording or not self.audio_frames:
            return 0
        
        total_samples = sum(len(frame) for frame in self.audio_frames)
        duration = total_samples / self.sample_rate
        return duration

    def cleanup(self):
        """Clean up resources"""
        logger.debug("Cleaning up audio recorder resources")
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
        self.is_recording = False
        self.audio_frames = []