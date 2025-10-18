"""
ElevenLabs TTS Integration for GhostBack.ai
Handles voice cloning and TTS generation using ElevenLabs API
"""

import streamlit as st
import tempfile
import os
import io
import base64
from typing import Dict, Any, Optional
import requests
from elevenlabs import ElevenLabs, VoiceSettings, Voice
import time

class ElevenLabsIntegration:
    """Integrates ElevenLabs TTS with voice cloning capabilities."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = None
        self.voice_name = None
        self.voice_settings = None
        
    def clone_voice_from_audio(self, audio_data: bytes, voice_name: str = None) -> Dict[str, Any]:
        """Clone a voice from uploaded audio data."""
        
        try:
            if not voice_name:
                voice_name = f"GhostBack_Voice_{int(time.time())}"
            
            # Validate audio data
            if not audio_data or len(audio_data) == 0:
                return {
                    "success": False,
                    "error": "No audio data provided",
                    "voice_id": None
                }
            
            # Create temporary file for audio - try to preserve original format
            # Determine file extension from audio data or use WAV as fallback
            file_extension = "wav"
            
            # Try to detect if it's already a valid audio format
            if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb'):
                file_extension = "mp3"
            elif audio_data.startswith(b'RIFF'):
                file_extension = "wav"
            elif audio_data.startswith(b'ftypM4A') or audio_data.startswith(b'\x00\x00\x00\x20ftypM4A'):
                file_extension = "m4a"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_data)
                temp_file.flush()  # Ensure data is written
            
            try:
                # Debug: Check file size and format
                file_size = os.path.getsize(temp_path)
                print(f"📁 Created temp file: {temp_path}")
                print(f"📊 File size: {file_size:,} bytes")
                print(f"🎵 File extension: {file_extension}")
                
                # Clone voice using ElevenLabs Instant Voice Cloning (IVC) API
                # Open the file and pass as file object
                with open(temp_path, 'rb') as audio_file:
                    voice_response = self.client.voices.ivc.create(
                        name=voice_name,
                        files=[audio_file],  # Pass file object
                        description=f"Voice cloned from audio sample for GhostBack.ai",
                        remove_background_noise=True
                    )
                
                # Extract voice ID from IVC response
                self.voice_id = voice_response.voice_id
                self.voice_name = voice_name
                
                # Set default voice settings
                self.voice_settings = VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
                
                return {
                    "success": True,
                    "voice_id": voice_response.voice_id,
                    "voice_name": voice_name,
                    "message": f"Voice '{voice_name}' cloned successfully!"
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            # If the first attempt fails, try converting to WAV using pydub
            try:
                print(f"⚠️ First attempt failed: {str(e)}")
                print("🔄 Trying audio conversion with pydub...")
                
                # Convert audio to WAV using pydub
                from pydub import AudioSegment
                import io
                
                # Load audio from bytes
                audio = AudioSegment.from_file(io.BytesIO(audio_data))
                
                # Convert to WAV
                wav_data = io.BytesIO()
                audio.export(wav_data, format="wav")
                wav_data.seek(0)
                
                # Create new temp file with converted audio
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_path = temp_file.name
                    temp_file.write(wav_data.read())
                    temp_file.flush()
                
                print(f"📁 Created converted WAV file: {temp_path}")
                print(f"📊 Converted file size: {os.path.getsize(temp_path):,} bytes")
                
                # Try again with converted file
                with open(temp_path, 'rb') as audio_file:
                    voice_response = self.client.voices.ivc.create(
                        name=voice_name,
                        files=[audio_file],
                        description=f"Voice cloned from audio sample for GhostBack.ai",
                        remove_background_noise=True
                    )
                
                # Extract voice ID from IVC response
                self.voice_id = voice_response.voice_id
                self.voice_name = voice_name
                
                # Set default voice settings
                self.voice_settings = VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
                
                return {
                    "success": True,
                    "voice_id": voice_response.voice_id,
                    "voice_name": voice_name,
                    "message": f"Voice '{voice_name}' cloned successfully! (converted to WAV)"
                }
                
            except Exception as e2:
                return {
                    "success": False,
                    "error": f"Voice cloning failed: {str(e)}. Conversion also failed: {str(e2)}",
                    "voice_id": None
                }
    
    def generate_speech(self, text: str, voice_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate speech using the cloned voice."""
        
        try:
            if not self.voice_id:
                return {
                    "success": False,
                    "error": "No voice cloned. Please upload and clone a voice first."
                }
            
            # Use provided settings or default
            if voice_settings:
                settings = VoiceSettings(
                    stability=voice_settings.get('stability', 0.5),
                    similarity_boost=voice_settings.get('similarity_boost', 0.75),
                    style=voice_settings.get('style', 0.0),
                    use_speaker_boost=voice_settings.get('use_speaker_boost', True)
                )
            else:
                settings = self.voice_settings
            
            # Generate speech
            audio = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=settings
            )
            
            # Convert generator to bytes
            audio_data = b"".join(audio)
            
            return {
                "success": True,
                "audio_data": audio_data,
                "text": text,
                "voice_id": self.voice_id,
                "voice_name": self.voice_name,
                "format": "mp3",
                "file_size": len(audio_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Speech generation failed: {str(e)}"
            }
    
    def get_voice_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current cloned voice."""
        
        if not self.voice_id:
            return None
        
        try:
            voice = self.client.voices.get(self.voice_id)
            return {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "description": voice.description,
                "category": voice.category,
                "settings": {
                    "stability": voice.settings.stability,
                    "similarity_boost": voice.settings.similarity_boost,
                    "style": voice.settings.style,
                    "use_speaker_boost": voice.settings.use_speaker_boost
                }
            }
        except Exception as e:
            return {
                "error": f"Failed to get voice info: {str(e)}"
            }
    
    def update_voice_settings(self, settings: Dict[str, Any]) -> bool:
        """Update voice settings for the cloned voice."""
        
        try:
            if not self.voice_id:
                return False
            
            voice_settings = VoiceSettings(
                stability=settings.get('stability', 0.5),
                similarity_boost=settings.get('similarity_boost', 0.75),
                style=settings.get('style', 0.0),
                use_speaker_boost=settings.get('use_speaker_boost', True)
            )
            
            self.voice_settings = voice_settings
            return True
            
        except Exception as e:
            print(f"Failed to update voice settings: {e}")
            return False
    
    def delete_voice(self) -> bool:
        """Delete the cloned voice from ElevenLabs."""
        
        try:
            if not self.voice_id:
                return False
            
            self.client.voices.delete(self.voice_id)
            self.voice_id = None
            self.voice_name = None
            self.voice_settings = None
            
            return True
            
        except Exception as e:
            print(f"Failed to delete voice: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the ElevenLabs API connection."""
        
        try:
            # Try a simple text-to-speech call with a default voice
            # This tests if the API key works for the core functionality
            test_audio = self.client.text_to_speech.convert(
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Default voice ID
                text="Hello, this is a test.",
                model_id="eleven_multilingual_v2"
            )
            
            # If we get here, the API key works
            return {
                "success": True,
                "message": "ElevenLabs API key is valid and working!",
                "test_audio_size": len(b"".join(test_audio))
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"API test failed: {str(e)}"
            }
