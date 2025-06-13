import os
import logging
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS")

# Voice ID Configuration
VOICE_CONFIG = {
    "english": {
        "male": "NNl6r8mD7vthiJatiJt1",
        "female": "2zRM7PkgwBPiau2jvVXc"
    },
    "spanish": {
        "male": "15bJsujCI3tcDWeoZsQP",  # Your voice
        "female": "x5IDPSl4ZUbhosMmVFTk"
    }
}

# Bilingual Interface Text
INTERFACE_TEXT = {
    "english": {
        "app_title": "🌍 BiLingual AI",
        "app_subtitle": "Real-time voice translation",
        "translation_mode": "🌐 Translation Mode",
        "voice_selection": "🎭 Voice Selection",
        "male": "Male",
        "female": "Female", 
        "ready_to_translate": "Ready to translate",
        "tap_to_record": "🎤 Tap to Record",
        "stop_recording": "🛑 Stop Recording",
        "recording": "🔴 Recording... Click to stop",
        "processing": "Processing audio...",
        "generating_audio": "Generating audio...",
        "translation_results": "📝 Translation Results",
        "audio_player": "🎵 Audio Player",
        "settings": "⚙️ Settings",
        "auto_play": "🔊 Auto-play translations",
        "auto_play_help": "Automatically play audio when translation is complete",
        "original": "Original",
        "translation": "Translation",
        "audio_recorded": "Audio recorded",
        "copy_text": "Copy text",
        "language_switch": "🌐 Interface Language"
    },
    "spanish": {
        "app_title": "🌍 BiLingual AI", 
        "app_subtitle": "Traducción de voz en tiempo real",
        "translation_mode": "🌐 Modo de Traducción",
        "voice_selection": "🎭 Selección de Voz",
        "male": "Masculino",
        "female": "Femenino",
        "ready_to_translate": "Listo para traducir",
        "tap_to_record": "🎤 Presiona para Grabar",
        "stop_recording": "🛑 Detener Grabación", 
        "recording": "🔴 Grabando... Presiona para detener",
        "processing": "Procesando audio...",
        "generating_audio": "Generando audio...",
        "translation_results": "📝 Resultados de Traducción",
        "audio_player": "🎵 Reproductor de Audio",
        "settings": "⚙️ Configuración",
        "auto_play": "🔊 Reproducir traducciones automáticamente",
        "auto_play_help": "Reproducir audio automáticamente cuando se complete la traducción",
        "original": "Original",
        "translation": "Traducción",
        "audio_recorded": "Audio grabado",
        "copy_text": "Copiar texto",
        "language_switch": "🌐 Idioma de la Interfaz"
    }
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ENABLE_VERBOSE_LOGGING = os.getenv("ENABLE_VERBOSE_LOGGING", "FALSE").upper() == "TRUE"

# Audio Configuration
AUDIO_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_SAMPLE_WIDTH = 2

# Setup logging
def setup_logging():
    """Setup minimal logging for essential info only"""
    log_format = "%(asctime)s | %(levelname)8s | %(name)20s | %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.WARNING,  # Set root to WARNING to silence third-party libs
        format=log_format,
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Silence noisy third-party loggers
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING) 
    logging.getLogger('groq').setLevel(logging.WARNING)
    logging.getLogger('watchdog').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Create specialized loggers
    loggers = {
        'audio': logging.getLogger('bilingual.audio'),
        'transcription': logging.getLogger('bilingual.transcription'), 
        'tts': logging.getLogger('bilingual.tts'),
        'ui': logging.getLogger('bilingual.ui'),
        'api': logging.getLogger('bilingual.api')
    }
    
    # Set levels based on what user wants to see
    if ENABLE_VERBOSE_LOGGING:
        for logger in loggers.values():
            logger.setLevel(logging.DEBUG)
    else:
        # Only essential logs
        loggers['audio'].setLevel(logging.INFO)    # Recording on/off
        loggers['transcription'].setLevel(logging.INFO) # API confirmations
        loggers['api'].setLevel(logging.INFO)      # API call confirmations
        loggers['tts'].setLevel(logging.INFO)      # TTS status
        loggers['ui'].setLevel(logging.WARNING)    # Only errors
    
    return loggers

# Initialize loggers
LOGGERS = setup_logging()