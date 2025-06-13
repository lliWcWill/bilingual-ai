import streamlit as st
import time
import os
import tempfile
import requests
from gtts import gTTS
import pygame
from audio_handler_streamlit import StreamlitAudioRecorder
from transcription import Transcriber
from config import LOGGERS, ELEVEN_LABS_API_KEY, VOICE_CONFIG, INTERFACE_TEXT
from audio_player import create_audio_player
# Audio player for TTS playback

# Get UI logger
ui_logger = LOGGERS['ui']
tts_logger = LOGGERS['tts']

# Page config optimized for mobile
st.set_page_config(
    page_title="BiLingual AI",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2d2d2d 100%);
        color: #e0e0e0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00d4ff, #0099cc, #006d99);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
    }
    
    .main-subtitle {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.2rem;
        font-weight: 400;
    }
    
    /* Status card - now clickable */
    .status-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 1.5rem;
        padding: 2rem;
        margin: 2rem 0 4rem 0;
        border: 1px solid #404040;
        box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.1), 0 8px 25px rgba(0,0,0,0.4);
        text-align: center;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .status-card:hover {
        transform: translateY(-2px);
        box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.2), 0 12px 35px rgba(0,0,0,0.5);
        border-color: #505050;
    }
    
    .status-card.recording {
        border: 2px solid #00d4ff;
        box-shadow: 
            inset 0 1px 0 0 rgba(255,255,255,0.2), 
            0 12px 35px rgba(0,0,0,0.5),
            0 0 0 4px rgba(0, 212, 255, 0.3),
            0 0 30px rgba(0, 212, 255, 0.4);
        animation: recording-glow 2s infinite;
    }
    
    .status-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, transparent, rgba(0, 212, 255, 0.4), transparent);
        border-radius: 1.5rem;
        z-index: -1;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .status-card.recording::before {
        opacity: 1;
        animation: border-flow 3s linear infinite;
    }
    
    .status-text {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .status-recording {
        color: #ff4444;
        animation: pulse 2s infinite;
        text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
    }
    
    .status-ready {
        color: #00d4ff;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }
    
    .microphone-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.8;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #00d4ff, #0099cc) !important;
        color: #0f0f0f !important;
        border: none !important;
        border-radius: 0.75rem !important;
        padding: 1.25rem 3rem !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3), inset 0 1px 0 0 rgba(255,255,255,0.2) !important;
        margin: 1rem 0 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.5), inset 0 1px 0 0 rgba(255,255,255,0.3) !important;
        background: linear-gradient(135deg, #00e5ff, #00aadd) !important;
    }
    
    /* Language cards */
    .language-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 1.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #404040;
        box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.1), 0 4px 15px rgba(0,0,0,0.3);
        position: relative;
        overflow: visible;
    }
    
    .card-actions {
        position: absolute;
        top: 1rem;
        right: 1rem;
        display: flex;
        gap: 0.5rem;
    }
    
    .copy-btn {
        background: rgba(0, 212, 255, 0.2);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 0.5rem;
        padding: 0.5rem;
        color: #00d4ff;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.8rem;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .copy-btn:hover {
        background: rgba(0, 212, 255, 0.3);
        transform: scale(1.1);
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.4);
    }
    
    .language-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00d4ff, #0099cc, #006d99);
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        gap: 0.75rem;
    }
    
    .card-flag {
        font-size: 1.5rem;
    }
    
    .card-title {
        color: #f0f0f0;
        font-weight: 600;
        font-size: 1.1rem;
        margin: 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    
    .card-text {
        color: #d0d0d0;
        font-size: 1rem;
        line-height: 1.6;
        margin: 0;
    }
    
    /* Section headers */
    h1, h2, h3 {
        color: white !important;
        text-align: center;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        border: 1px solid #404040 !important;
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.3) !important;
    }
    
    /* Help text styling */
    .stTextArea > div > div > small {
        color: #00d4ff !important;
        opacity: 0.8;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 0.5rem !important;
    }
    
    .stSelectbox label {
        color: white !important;
        font-weight: 600 !important;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes recording-glow {
        0%, 100% { 
            box-shadow: 
                inset 0 1px 0 0 rgba(255,255,255,0.2), 
                0 12px 35px rgba(0,0,0,0.5),
                0 0 0 4px rgba(0, 212, 255, 0.3),
                0 0 30px rgba(0, 212, 255, 0.4);
        }
        50% { 
            box-shadow: 
                inset 0 1px 0 0 rgba(255,255,255,0.2), 
                0 12px 35px rgba(0,0,0,0.5),
                0 0 0 6px rgba(0, 212, 255, 0.5),
                0 0 40px rgba(0, 212, 255, 0.6);
        }
    }
    
    @keyframes border-flow {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .waveform-animation {
        display: inline-block;
        margin: 0 2px;
        font-size: 1.5rem;
        animation: wave-bounce 1s infinite ease-in-out;
    }
    
    .waveform-animation:nth-child(2) { animation-delay: 0.1s; }
    .waveform-animation:nth-child(3) { animation-delay: 0.2s; }
    .waveform-animation:nth-child(4) { animation-delay: 0.3s; }
    
    @keyframes wave-bounce {
        0%, 100% { transform: scaleY(1); }
        50% { transform: scaleY(1.5); color: #00e5ff; }
    }
    
    @keyframes pulse {
        0%, 100% { 
            transform: scale(1); 
            filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.8));
        }
        50% { 
            transform: scale(1.1); 
            filter: drop-shadow(0 0 20px rgba(255, 215, 0, 1));
        }
    }
    
    /* Modern Audio Visualizer */
    .audio-visualizer-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 200px;
        position: relative;
        margin: 2rem 0;
    }
    
    .floating-audio-rings {
        position: relative;
        width: 120px;
        height: 120px;
        margin-bottom: 1rem;
    }
    
    .audio-ring {
        position: absolute;
        border-radius: 50%;
        border: 2px solid transparent;
        opacity: 0.6;
    }
    
    .audio-ring.outer {
        width: 120px;
        height: 120px;
        border-color: rgba(0, 212, 255, 0.4);
        animation: pulse-ring 3s ease-in-out infinite;
    }
    
    .audio-ring.middle {
        width: 80px;
        height: 80px;
        top: 20px;
        left: 20px;
        border-color: rgba(0, 212, 255, 0.6);
        animation: pulse-ring 2s ease-in-out infinite 0.5s;
    }
    
    .audio-ring.inner {
        width: 40px;
        height: 40px;
        top: 40px;
        left: 40px;
        border-color: rgba(0, 212, 255, 0.8);
        animation: pulse-ring 1.5s ease-in-out infinite 1s;
    }
    
    .audio-ring.recording {
        border-color: rgba(255, 68, 68, 0.8);
        box-shadow: 0 0 20px rgba(255, 68, 68, 0.3);
    }
    
    .audio-spectrum {
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 4px;
        height: 60px;
        margin-top: 1rem;
    }
    
    .spectrum-bar {
        width: 4px;
        background: linear-gradient(to top, #00d4ff, #0099cc);
        border-radius: 2px;
        transition: height 0.2s ease;
    }
    
    .spectrum-bar:nth-child(1) { height: 20px; animation: spectrum-bounce 1.2s ease-in-out infinite; }
    .spectrum-bar:nth-child(2) { height: 35px; animation: spectrum-bounce 1.0s ease-in-out infinite 0.1s; }
    .spectrum-bar:nth-child(3) { height: 50px; animation: spectrum-bounce 0.8s ease-in-out infinite 0.2s; }
    .spectrum-bar:nth-child(4) { height: 45px; animation: spectrum-bounce 1.1s ease-in-out infinite 0.3s; }
    .spectrum-bar:nth-child(5) { height: 60px; animation: spectrum-bounce 0.9s ease-in-out infinite 0.4s; }
    .spectrum-bar:nth-child(6) { height: 40px; animation: spectrum-bounce 1.3s ease-in-out infinite 0.5s; }
    .spectrum-bar:nth-child(7) { height: 25px; animation: spectrum-bounce 1.1s ease-in-out infinite 0.6s; }
    
    .spectrum-bar.recording {
        background: linear-gradient(to top, #ff4444, #ff6666);
        animation-duration: 0.3s;
    }
    
    @keyframes pulse-ring {
        0%, 100% { 
            transform: scale(1);
            opacity: 0.6;
        }
        50% { 
            transform: scale(1.2);
            opacity: 0.8;
        }
    }
    
    @keyframes spectrum-bounce {
        0%, 100% { 
            transform: scaleY(0.5);
            opacity: 0.7;
        }
        50% { 
            transform: scaleY(1);
            opacity: 1;
        }
    }
    
    .center-microphone {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 2rem;
        color: #00d4ff;
        z-index: 10;
        filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.5));
    }
    
    .center-microphone.recording {
        color: #ff4444;
        filter: drop-shadow(0 0 15px rgba(255, 68, 68, 0.7));
        animation: mic-glow 1s ease-in-out infinite;
    }
    
    @keyframes mic-glow {
        0%, 100% { 
            transform: translate(-50%, -50%) scale(1);
        }
        50% { 
            transform: translate(-50%, -50%) scale(1.1);
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    ui_logger.debug("Initializing session state variables")
    
    defaults = {
        'recording': False,
        'audio_file': None,
        'transcription': "",
        'translation': "",
        'auto_play': False,
        'language_mode': "English → Spanish",
        'recording_start_time': None,
        'last_error': None,
        'interface_language': 'english',  # english or spanish
        'selected_voice_gender': 'male'   # male or female
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
            ui_logger.debug(f"Initialized session state: {key} = {default_value}")

init_session_state()

# Initialize components
@st.cache_resource
def get_audio_recorder():
    ui_logger.info("Initializing audio recorder")
    return StreamlitAudioRecorder()

@st.cache_resource(show_spinner=False)
def get_transcriber(version="v2_with_bidirectional_translation"):
    ui_logger.info("Initializing transcriber with translate_text_to_english support")
    return Transcriber()

recorder = get_audio_recorder()
transcriber = get_transcriber()

def text_to_speech(text, lang='es'):
    """Convert text to speech using ElevenLabs with voice selection based on language and gender"""
    # Ensure text is a proper string
    text = str(text or "")
    
    # Check if text contains DeltaGenerator or is invalid
    if "DeltaGenerator" in text or not text.strip():
        tts_logger.error(f"Invalid text for TTS: {text[:100]}")
        return None
        
    tts_logger.info(f"Starting TTS: lang={lang}, text_length={len(text)}")
    tts_logger.debug(f"TTS text preview: '{text[:100]}...'")
    
    try:
        # Determine voice based on language and selected gender
        voice_lang = "spanish" if lang == 'es' else "english"
        gender = st.session_state.selected_voice_gender
        voice_id = VOICE_CONFIG[voice_lang][gender]
        
        # Always use ElevenLabs now for both languages
        tts_logger.info(f"Using ElevenLabs TTS: {voice_lang} {gender} voice ({voice_id})")
        return eleven_labs_tts(text, voice_id)
        
    except Exception as e:
        tts_logger.error(f"TTS generation failed: {e}")
        return None

def eleven_labs_tts(text, voice_id):
    """Generate TTS using ElevenLabs API with specified voice"""
    tts_logger.info(f"Generating ElevenLabs TTS for voice {voice_id}")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        tts_logger.debug(f"Making ElevenLabs API request: {url}")
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            fp.write(response.content)
            file_size = len(response.content)
            tts_logger.info(f"ElevenLabs audio generated: {fp.name} ({file_size} bytes)")
            
            # Validate it's actually MP3 audio
            if file_size < 100:
                tts_logger.error(f"ElevenLabs audio file too small: {file_size} bytes")
                return None
            
            # Check first few bytes for MP3 signature
            fp.seek(0)
            header = fp.read(4)
            if not (header.startswith(b'ID3') or header.startswith(b'\xff\xfb')):
                tts_logger.error(f"Invalid MP3 header from ElevenLabs: {header}")
                return None
                
            return fp.name
            
    except requests.exceptions.RequestException as e:
        tts_logger.error(f"ElevenLabs API request failed: {e}")
        return None
    except Exception as e:
        tts_logger.error(f"ElevenLabs TTS generation failed: {e}")
        return None

def play_audio(file_path):
    """Play audio file with logging"""
    tts_logger.info(f"Playing audio: {file_path}")
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        tts_logger.info("Audio playback started successfully")
        return True
    except Exception as e:
        tts_logger.error(f"Audio playback failed: {e}")
        return False

# Main UI
def main():
    ui_logger.info("Rendering main UI")
    
    # Get current interface language and text
    interface_lang = st.session_state.interface_language
    text = INTERFACE_TEXT[interface_lang]
    
    # Language Switch at the top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        interface_options = ["English", "Español"]
        current_index = 0 if interface_lang == 'english' else 1
        selected_interface = st.selectbox(
            text["language_switch"],
            interface_options,
            index=current_index,
            key="interface_lang_select"
        )
        
        # Update interface language if changed
        new_interface_lang = 'english' if selected_interface == 'English' else 'spanish'
        if new_interface_lang != st.session_state.interface_language:
            st.session_state.interface_language = new_interface_lang
            
            # Auto-update translation mode based on interface language
            if new_interface_lang == 'english':
                st.session_state.language_mode = "English → Spanish"
            else:
                st.session_state.language_mode = "Spanish → English"
            
            # Clear previous results
            st.session_state.transcription = ""
            st.session_state.translation = ""
            st.rerun()
    
    # Header with Groq branding
    st.markdown(f"""
    <div class="main-header">
        <h1 class="main-title">{text["app_title"]}</h1>
        <p class="main-subtitle">{text["app_subtitle"]}</p>
        <div style="
            margin-top: 1rem; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 0.5rem;
            opacity: 0.9;
        ">
            <span style="
                color: #FFD700; 
                font-size: 1.4rem; 
                filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.6));
                animation: pulse 2s infinite;
            ">⚡</span>
            <span style="
                color: rgba(255, 255, 255, 0.8); 
                font-size: 1rem; 
                font-weight: 500;
                letter-spacing: 0.5px;
                font-family: 'Inter', sans-serif;
            ">
                Powered by <span style="
                    color: #F55036;
                    font-weight: 800;
                    font-size: 1.4rem;
                    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
                    text-shadow: 0 0 15px rgba(245, 80, 54, 0.4);
                    font-family: 'Inter', sans-serif;
                    letter-spacing: 0.5px;
                ">Groq</span>
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Language mode selector
    new_mode = st.selectbox(
        text["translation_mode"],
        ["English → Spanish", "Spanish → English"],
        index=0 if st.session_state.language_mode == "English → Spanish" else 1,
        key="lang_mode_select"
    )
    
    if new_mode != st.session_state.language_mode:
        ui_logger.info(f"Language mode changed: {st.session_state.language_mode} → {new_mode}")
        st.session_state.language_mode = new_mode
        # Clear previous results
        st.session_state.transcription = ""
        st.session_state.translation = ""
    
    # Auto-play toggle (moved up)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Custom auto-play toggle
        autoplay_status = "ON" if st.session_state.auto_play else "OFF"
        autoplay_color = "#00d4ff" if st.session_state.auto_play else "#666666"
        
        st.markdown(f"""
        <div style="text-align: center; margin: 1rem 0;">
            <span style="color: #e0e0e0; font-weight: 600;">🔊 {text["auto_play"].replace('🔊 ', '')}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Auto-play: {autoplay_status}", key="autoplay_toggle", use_container_width=True):
            st.session_state.auto_play = not st.session_state.auto_play
            st.rerun()

    # Voice Selection (between auto-play and status card)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"### {text['voice_selection']}")
        
        # Custom voice buttons with fixed sizing
        st.markdown("""
        <style>
        .voice-button-container {
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
        }
        .voice-button {
            flex: 1;
            padding: 0.75rem;
            border-radius: 0.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 600;
            font-size: 0.9rem;
            border: 2px solid;
        }
        .voice-button.selected {
            background: linear-gradient(135deg, #00d4ff, #0099cc);
            color: #0f0f0f;
            border-color: #00d4ff;
        }
        .voice-button.unselected {
            background: #2d2d2d;
            color: #e0e0e0;
            border-color: #404040;
        }
        .voice-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)
        
        voice_col1, voice_col2 = st.columns(2)
        
        # Add CSS for voice button sizing and font adjustments
        st.markdown("""
        <style>
        /* Force equal button sizing and smaller font for Spanish */
        .stButton > button {
            height: 3rem !important;
            font-size: 0.9rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with voice_col1:
            male_selected = st.button(
                f"👨 {text['male']}", 
                key="male_voice_btn",
                type="primary" if st.session_state.selected_voice_gender == "male" else "secondary",
                use_container_width=True,
                disabled=st.session_state.selected_voice_gender == "male"
            )
            if male_selected:
                st.session_state.selected_voice_gender = "male"
                st.rerun()
            
            # Confirmation message for male
            if st.session_state.selected_voice_gender == "male":
                confirmation = "Got it!" if interface_lang == 'english' else "¡Entendido!"
                st.markdown(f"<div style='text-align: center; color: #00d4ff; font-size: 0.8rem; margin-top: 0.5rem;'>✓ {confirmation}</div>", unsafe_allow_html=True)
        
        with voice_col2:
            female_selected = st.button(
                f"👩 {text['female']}", 
                key="female_voice_btn", 
                type="primary" if st.session_state.selected_voice_gender == "female" else "secondary",
                use_container_width=True,
                disabled=st.session_state.selected_voice_gender == "female"
            )
            if female_selected:
                st.session_state.selected_voice_gender = "female"
                st.rerun()
                
            # Confirmation message for female
            if st.session_state.selected_voice_gender == "female":
                confirmation = "Got it!" if interface_lang == 'english' else "¡Entendido!"
                st.markdown(f"<div style='text-align: center; color: #00d4ff; font-size: 0.8rem; margin-top: 0.5rem;'>✓ {confirmation}</div>", unsafe_allow_html=True)
    
    # Status display with modern audio visualizer
    duration_text = ""
    if st.session_state.recording and st.session_state.recording_start_time:
        duration = time.time() - st.session_state.recording_start_time
        duration_text = f" ({duration:.1f}s)"
    
    if st.session_state.recording:
        status_class = "status-recording"
        status_text = f"{text['recording']}{duration_text}"
        card_class = "status-card recording"
        ring_class = "recording"
        spectrum_class = "recording"
        mic_class = "recording"
    else:
        status_class = "status-ready"
        status_text = f"{text['ready_to_translate']}: {st.session_state.language_mode}"
        card_class = "status-card"
        ring_class = ""
        spectrum_class = ""
        mic_class = ""
    
    # Modern audio visualizer status display
    st.markdown(f"""
    <div class="{card_class}">
        <div class="audio-visualizer-container">
            <div class="floating-audio-rings">
                <div class="audio-ring outer {ring_class}"></div>
                <div class="audio-ring middle {ring_class}"></div>
                <div class="audio-ring inner {ring_class}"></div>
                <div class="center-microphone {mic_class}">🎙️</div>
            </div>
            <div class="audio-spectrum">
                <div class="spectrum-bar {spectrum_class}"></div>
                <div class="spectrum-bar {spectrum_class}"></div>
                <div class="spectrum-bar {spectrum_class}"></div>
                <div class="spectrum-bar {spectrum_class}"></div>
                <div class="spectrum-bar {spectrum_class}"></div>
                <div class="spectrum-bar {spectrum_class}"></div>
                <div class="spectrum-bar {spectrum_class}"></div>
            </div>
        </div>
        <div class="status-text {status_class}">{status_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Recording button with minimal styling to blend in
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        button_text = text["tap_to_record"] if not st.session_state.recording else text["stop_recording"]
        if st.button(button_text, key="main_recording_btn", use_container_width=True):
            if not st.session_state.recording:
                ui_logger.info("User started recording")
                if recorder.start_recording():
                    st.session_state.recording = True
                    st.session_state.recording_start_time = time.time()
                    ui_logger.info("Recording started successfully")
                    st.rerun()
                else:
                    ui_logger.error("Failed to start recording")
                    st.session_state.last_error = "Failed to start recording"
            else:
                ui_logger.info("User stopped recording")
                st.session_state.recording = False
                
                # Process audio
                with st.spinner("Processing audio..."):
                    ui_logger.info("Processing recorded audio")
                    audio_file = recorder.stop_recording()
                    
                    if audio_file:
                        ui_logger.info(f"Audio processing successful: {audio_file}")
                        st.session_state.audio_file = audio_file
                        
                        if st.session_state.language_mode == "English → Spanish":
                            ui_logger.info("Starting English → Spanish translation workflow")
                            # English to Spanish
                            english_text = transcriber.transcribe_audio(audio_file, language="en")
                            st.session_state.transcription = english_text
                            
                            if english_text and not english_text.startswith("Error"):
                                spanish_text = transcriber.translate_text_to_spanish(english_text)
                                st.session_state.translation = spanish_text
                                ui_logger.info("English → Spanish workflow completed")
                            else:
                                ui_logger.error(f"Transcription failed: {english_text}")
                        else:
                            ui_logger.info("Starting Spanish → English translation workflow")
                            # Spanish to English  
                            english_translation = transcriber.translate_audio(audio_file)
                            st.session_state.translation = english_translation
                            st.session_state.transcription = "Spanish audio"
                            ui_logger.info("Spanish → English workflow completed")
                    else:
                        ui_logger.error("Audio processing failed - no file returned")
                        st.session_state.last_error = "Failed to process audio"
                
                st.rerun()
    
    
    # Add some spacing before results
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Results display
    if st.session_state.transcription or st.session_state.translation:
        st.markdown("---")
        st.markdown(f"## {text['translation_results']}")
        
        if st.session_state.language_mode == "English → Spanish":
            # English editable card with embedded copy
            st.markdown(f"""
            <div class="language-card">
                <div class="card-header">
                    <span class="card-flag">🇺🇸</span>
                    <h3 class="card-title">English ({text["original"]})</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Editable text area for English
            english_text = st.text_area(
                "English Text",
                value=str(st.session_state.transcription or ""),
                height=100,
                key="english_edit",
                placeholder="Type English text here or record audio above...",
                label_visibility="collapsed",
                help="📋 Select all text with Ctrl+A (or Cmd+A) then copy with Ctrl+C (or Cmd+C)"
            )
            
            # Update session state if text changed
            if english_text != st.session_state.transcription:
                st.session_state.transcription = english_text
            
            # Translate button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Translate to Spanish", key="translate_english", use_container_width=True):
                    # Use the text from the text area, not session state
                    current_text = str(english_text or "")
                    if current_text.strip():
                        with st.spinner(text["generating_audio"]):
                            # Translate the edited English text
                            spanish_translation = transcriber.translate_text_to_spanish(current_text.strip())
                            st.session_state.translation = spanish_translation
                            st.rerun()
            
            # Spanish editable card with embedded copy
            st.markdown(f"""
            <div class="language-card">
                <div class="card-header">
                    <span class="card-flag">🇪🇸</span>
                    <h3 class="card-title">Spanish ({text["translation"]})</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Editable text area for Spanish
            spanish_text = st.text_area(
                "Spanish Text",
                value=str(st.session_state.translation or ""),
                height=100,
                key="spanish_edit",
                placeholder="La traducción aparecerá aquí o escribe directamente...",
                label_visibility="collapsed",
                help="📋 Select all text with Ctrl+A (or Cmd+A) then copy with Ctrl+C (or Cmd+C)"
            )
            
            # Update session state if text changed
            if spanish_text != st.session_state.translation:
                st.session_state.translation = spanish_text
            
            # Translate button (Spanish to English)
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Translate to English", key="translate_spanish", use_container_width=True):
                    # Use the text from the text area, not session state
                    current_text = str(spanish_text or "")
                    if current_text.strip():
                        with st.spinner(text["generating_audio"]):
                            # Translate the edited Spanish text to English
                            english_translation = transcriber.translate_text_to_english(current_text.strip())
                            st.session_state.transcription = english_translation
                            st.rerun()
            
            # Play Spanish audio with custom player
            translation_text = str(st.session_state.translation or "")
            if translation_text and not translation_text.startswith("Error"):
                st.markdown(f"### {text['audio_player']}")
                
                # Generate TTS audio
                with st.spinner(text["generating_audio"]):
                    audio_path = text_to_speech(translation_text, 'es')
                    if audio_path:
                        tts_logger.info(f"Generated Spanish TTS audio: {audio_path}")
                        # Check if auto-play is enabled
                        should_autoplay = st.session_state.auto_play and not st.session_state.recording
                        if should_autoplay:
                            tts_logger.info("Auto-playing translation")
                        create_audio_player(audio_path, "Spanish Translation", autoplay=should_autoplay)
                    else:
                        st.error("Failed to generate audio")
        else:
            # Spanish to English mode
            # Spanish card
            st.markdown(f"""
            <div class="language-card">
                <div class="card-header">
                    <span class="card-flag">🇪🇸</span>
                    <h3 class="card-title">Spanish ({text["original"]})</h3>
                </div>
                <div class="card-text">{text["audio_recorded"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # English editable card with embedded copy
            st.markdown(f"""
            <div class="language-card">
                <div class="card-header">
                    <span class="card-flag">🇺🇸</span>
                    <h3 class="card-title">English ({text["translation"]})</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Editable text area for English translation
            english_translation = st.text_area(
                "English Translation",
                value=str(st.session_state.translation or ""),
                height=100,
                key="english_translation_edit",
                placeholder="Translation will appear here or type directly...",
                label_visibility="collapsed",
                help="📋 Select all text with Ctrl+A (or Cmd+A) then copy with Ctrl+C (or Cmd+C)"
            )
            
            # Update session state if text changed
            if english_translation != st.session_state.translation:
                st.session_state.translation = english_translation
            
            # Refresh/retranslate button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Retranslate from Audio", key="retranslate_spanish", use_container_width=True):
                    if st.session_state.audio_file:
                        with st.spinner(text["generating_audio"]):
                            # Re-translate from Spanish audio
                            new_translation = transcriber.translate_audio(st.session_state.audio_file)
                            st.session_state.translation = new_translation
                            st.rerun()
            
            # Play English audio with custom player
            translation_text = str(st.session_state.translation or "")
            if translation_text and not translation_text.startswith("Error"):
                st.markdown(f"### {text['audio_player']}")
                
                # Generate TTS audio
                with st.spinner(text["generating_audio"]):
                    audio_path = text_to_speech(translation_text, 'en')
                    if audio_path:
                        tts_logger.info(f"Generated English TTS audio: {audio_path}")
                        # Check if auto-play is enabled
                        should_autoplay = st.session_state.auto_play and not st.session_state.recording
                        if should_autoplay:
                            tts_logger.info("Auto-playing translation")
                        create_audio_player(audio_path, "English Translation", autoplay=should_autoplay)
                    else:
                        st.error("Failed to generate audio")
    
    # Debug info (if there are errors)
    if st.session_state.last_error:
        st.error(st.session_state.last_error)
    
    ui_logger.debug("Main UI render completed")

if __name__ == "__main__":
    main()