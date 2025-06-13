import os
import time
from groq import Groq
import json
from config import GROQ_API_KEY, LOGGERS

# Get specialized loggers
transcription_logger = LOGGERS['transcription']
api_logger = LOGGERS['api']

class Transcriber:
    def __init__(self):
        transcription_logger.info("Initializing Transcriber with Groq API")
        try:
            self.client = Groq(api_key=GROQ_API_KEY)
            transcription_logger.info("Groq client initialized successfully")
        except Exception as e:
            transcription_logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def transcribe_audio(self, file_path, prompt=None, language="en"):
        """Transcribe audio file to text"""
        transcription_logger.info(f"Starting transcription: file={file_path}, language={language}")
        api_logger.debug(f"Transcription params: prompt={prompt}, model=whisper-large-v3")
        
        if not os.path.exists(file_path):
            transcription_logger.error(f"Audio file not found: {file_path}")
            return "Error: Audio file not found."

        try:
            # Get file info for logging
            file_size = os.path.getsize(file_path)
            transcription_logger.debug(f"Audio file size: {file_size} bytes")
            
            start_time = time.time()
            
            with open(file_path, "rb") as file:
                api_logger.info("Making API call to Groq transcription endpoint")
                transcription = self.client.audio.transcriptions.create(
                    file=(file_path, file.read()),
                    model="whisper-large-v3",
                    prompt=prompt,
                    response_format="json",
                    language=language,
                    temperature=0.0
                )
            
            api_time = time.time() - start_time
            api_logger.info(f"Transcription API call completed in {api_time:.2f}s")
            
            result_text = transcription.text
            transcription_logger.info(f"Transcription successful: '{result_text[:100]}...' ({len(result_text)} chars)")
            
            return result_text
            
        except Exception as e:
            transcription_logger.error(f"Transcription failed: {e}")
            api_logger.error(f"API Error details: {str(e)}")
            return f"Error during transcription: {str(e)}"

    def translate_audio(self, file_path, prompt=None):
        """Translate audio from any language to English"""
        transcription_logger.info(f"Starting audio translation: file={file_path}")
        api_logger.debug(f"Translation params: prompt={prompt}, model=whisper-large-v3")
        
        if not os.path.exists(file_path):
            transcription_logger.error(f"Audio file not found: {file_path}")
            return "Error: Audio file not found."

        try:
            file_size = os.path.getsize(file_path)
            transcription_logger.debug(f"Audio file size: {file_size} bytes")
            
            start_time = time.time()
            
            with open(file_path, "rb") as file:
                api_logger.info("Making API call to Groq translation endpoint")
                translation = self.client.audio.translations.create(
                    file=(file_path, file.read()),
                    model="whisper-large-v3",
                    prompt=prompt,
                    response_format="json",
                    temperature=0.0
                )
            
            api_time = time.time() - start_time
            api_logger.info(f"Translation API call completed in {api_time:.2f}s")
            
            result_text = translation.text
            transcription_logger.info(f"Translation successful: '{result_text[:100]}...' ({len(result_text)} chars)")
            
            return result_text
            
        except Exception as e:
            transcription_logger.error(f"Audio translation failed: {e}")
            api_logger.error(f"API Error details: {str(e)}")
            return f"Error during translation: {str(e)}"

    def translate_text_to_spanish(self, english_text):
        """Translate English text to Spanish using Llama 3.3 70B"""
        transcription_logger.info(f"Starting text translation to Spanish: '{english_text[:50]}...'")
        api_logger.debug(f"Text translation params: model=llama-3.3-70b-versatile, temp=0.1")
        
        try:
            start_time = time.time()
            
            api_logger.info("Making API call to Groq chat completion for Spanish translation")
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate the following English text to natural, conversational Spanish. Only return the Spanish translation, no explanations."
                    },
                    {
                        "role": "user", 
                        "content": english_text
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=1000
            )
            
            api_time = time.time() - start_time
            api_logger.info(f"Spanish translation API call completed in {api_time:.2f}s")
            
            result_text = chat_completion.choices[0].message.content.strip()
            transcription_logger.info(f"Spanish translation successful: '{result_text[:100]}...' ({len(result_text)} chars)")
            
            # Log usage if available
            if hasattr(chat_completion, 'usage'):
                api_logger.debug(f"Token usage: {chat_completion.usage}")
            
            return result_text
            
        except Exception as e:
            transcription_logger.error(f"Spanish translation failed: {e}")
            api_logger.error(f"API Error details: {str(e)}")
            return f"Error during text translation: {str(e)}"
    
    def translate_text_to_english(self, spanish_text):
        """Translate Spanish text to English using Llama 3.3 70B"""
        transcription_logger.info(f"Starting text translation to English: '{spanish_text[:50]}...'")
        api_logger.debug(f"Text translation params: model=llama-3.3-70b-versatile, temp=0.1")
        
        try:
            start_time = time.time()
            
            api_logger.info("Making API call to Groq chat completion for English translation")
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate the following Spanish text to natural, conversational English. Only return the English translation, no explanations."
                    },
                    {
                        "role": "user", 
                        "content": spanish_text
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=1000
            )
            
            duration = time.time() - start_time
            api_logger.info(f"Text translation API call completed in {duration:.2f}s")
            
            result_text = chat_completion.choices[0].message.content.strip()
            
            # Log usage if available
            if hasattr(chat_completion, 'usage'):
                api_logger.debug(f"Token usage: {chat_completion.usage}")
            
            transcription_logger.info(f"Translation successful: '{result_text[:100]}...' ({len(result_text)} chars)")
            
            return result_text
            
        except Exception as e:
            transcription_logger.error(f"English translation failed: {e}")
            api_logger.error(f"API Error details: {str(e)}")
            return f"Error during text translation: {str(e)}"