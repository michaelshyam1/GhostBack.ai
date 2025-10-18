"""
Text-to-Speech Integration for GhostBack.ai
Handles TTS generation with voice matching
"""

import streamlit as st
import tempfile
import os
from typing import Dict, Any, Optional
import base64
import io
import pyttsx3
from gtts import gTTS
from voice_analyzer import VoiceAnalyzer, TextToSpeechGenerator
from elevenlabs_integration import ElevenLabsIntegration

class TTSIntegration:
    """Integrates TTS functionality with the chat system."""
    
    def __init__(self, elevenlabs_api_key: str = None):
        self.voice_analyzer = VoiceAnalyzer()
        self.tts_generator = TextToSpeechGenerator()
        self.voice_profile = None
        self.engine = None
        self.elevenlabs = None
        self._init_tts_engine()
        
        # Initialize ElevenLabs if API key provided
        if elevenlabs_api_key:
            try:
                self.elevenlabs = ElevenLabsIntegration(elevenlabs_api_key)
                print("✅ ElevenLabs integration initialized")
            except Exception as e:
                print(f"⚠️ ElevenLabs initialization failed: {e}")
                self.elevenlabs = None
        else:
            # Try to use the default API key if none provided
            try:
                default_key = "sk_56f052abde4435779cd252bf82654fb333801488dacf9f75"
                self.elevenlabs = ElevenLabsIntegration(default_key)
                print("✅ ElevenLabs integration initialized with default key")
            except Exception as e:
                print(f"⚠️ ElevenLabs initialization with default key failed: {e}")
                self.elevenlabs = None
    
    def _init_tts_engine(self):
        """Initialize the TTS engine."""
        try:
            self.engine = pyttsx3.init()
            # Set default properties
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.8)  # Volume level (0.0 to 1.0)
        except Exception as e:
            st.warning(f"Could not initialize TTS engine: {e}")
            self.engine = None
    
    def process_voice_sample(self, uploaded_file) -> Dict[str, Any]:
        """Process uploaded voice sample and create voice profile."""
        
        if uploaded_file is None:
            return {"success": False, "error": "No file uploaded"}
        
        try:
            # Read audio data
            audio_data = uploaded_file.read()
            
            # Get file extension for better error handling
            file_extension = uploaded_file.name.split('.')[-1].lower() if hasattr(uploaded_file, 'name') else 'unknown'
            
            # Analyze voice
            analysis_result = self.voice_analyzer.analyze_voice_sample(audio_data, file_extension=file_extension)
            
            if not analysis_result["success"]:
                return {
                    "success": False, 
                    "error": f"Failed to analyze {file_extension.upper()} file: {analysis_result['error']}"
                }
            
            # Create voice profile
            self.voice_profile = self.voice_analyzer.create_voice_profile(analysis_result["features"])
            self.tts_generator.set_voice_profile(self.voice_profile)
            
            return {
                "success": True,
                "voice_profile": self.voice_profile,
                "features": analysis_result["features"],
                "duration": analysis_result["duration"],
                "file_format": file_extension
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error processing {file_extension.upper()} file: {str(e)}"}
    
    def generate_speech_for_message(self, message: str, is_ai_response: bool = False) -> Dict[str, Any]:
        """Generate speech parameters for a message."""
        
        if not self.voice_profile:
            return {"success": False, "error": "No voice profile available"}
        
        try:
            # Generate speech parameters
            parameters = self.tts_generator.generate_speech_parameters(message)
            
            # Add voice description
            voice_description = self.tts_generator.generate_voice_description(parameters)
            
            return {
                "success": True,
                "parameters": parameters,
                "voice_description": voice_description,
                "message": message,
                "is_ai_response": is_ai_response
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_voice_profile_summary(self) -> Optional[Dict[str, Any]]:
        """Get a summary of the current voice profile."""
        
        if not self.voice_profile:
            return None
        
        return {
            "voice_type": self.voice_profile["voice_quality"]["voice_type"],
            "emotional_tone": self.voice_profile["voice_quality"]["emotional_tone"],
            "base_pitch": self.voice_profile["pitch_characteristics"]["base_pitch"],
            "tempo": self.voice_profile["rhythm_characteristics"]["tempo"],
            "brightness": self.voice_profile["spectral_characteristics"]["brightness"],
            "clarity": self.voice_profile["voice_quality"]["clarity"]
        }
    
    def create_tts_instructions(self, parameters: Dict[str, Any]) -> str:
        """Create TTS instructions for external TTS services."""
        
        voice_type = parameters.get("voice_type", "warm_medium")
        pitch = parameters.get("pitch", 150)
        tempo = parameters.get("tempo", 120)
        energy = parameters.get("energy", 1.0)
        emotional_tone = parameters.get("emotional_tone", "neutral")
        
        # Map voice types to TTS voice names (adjust based on your TTS service)
        voice_mapping = {
            "bright_high": "en-US-AriaNeural",
            "warm_high": "en-US-JennyNeural", 
            "bright_medium": "en-US-GuyNeural",
            "warm_medium": "en-US-DavisNeural",
            "bright_low": "en-US-BrandonNeural",
            "warm_low": "en-US-ChristopherNeural"
        }
        
        # Map emotional tones to TTS styles
        style_mapping = {
            "excited": "excited",
            "sad": "sad",
            "angry": "angry",
            "happy": "cheerful",
            "calm": "calm",
            "neutral": "friendly"
        }
        
        voice_name = voice_mapping.get(voice_type, "en-US-DavisNeural")
        style = style_mapping.get(emotional_tone, "friendly")
        
        # Calculate pitch adjustment (relative to base pitch)
        pitch_adjustment = (pitch - 150) / 150  # Normalize around 150Hz
        
        instructions = {
            "voice": voice_name,
            "style": style,
            "pitch_adjustment": pitch_adjustment,
            "rate": tempo / 120,  # Normalize around 120 BPM
            "volume": min(energy, 1.0),
            "prosody": {
                "pitch": f"{pitch_adjustment:+.1f}Hz",
                "rate": f"{tempo/120:.1f}x",
                "volume": f"{min(energy, 1.0):.1f}"
            }
        }
        
        return instructions
    
    def generate_audio_simple(self, text: str) -> Dict[str, Any]:
        """Generate audio using a simpler approach that's less likely to hang."""
        
        try:
            if not self.engine:
                return {"success": False, "error": "TTS engine not available"}
            
            # Generate audio using pyttsx3 with a simpler approach
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_path = temp_file.name
            
            # Try a different approach - use the engine directly
            try:
                # Stop any existing speech
                self.engine.stop()
                
                # Configure voice based on profile if available - DO THIS RIGHT BEFORE GENERATION
                if self.voice_profile:
                    print(f"🎤 Applying voice profile: {self.voice_profile['voice_quality']['voice_type']}")
                    self._configure_voice_from_profile()
                    
                    # Verify settings were applied
                    current_rate = self.engine.getProperty('rate')
                    current_volume = self.engine.getProperty('volume')
                    current_voice = self.engine.getProperty('voice')
                    print(f"✅ Applied settings - Rate: {current_rate}, Volume: {current_volume}, Voice: {current_voice}")
                else:
                    print("⚠️ No voice profile available, using default settings")
                    self.engine.setProperty('rate', 150)
                    self.engine.setProperty('volume', 0.8)
                
                # Save to file
                self.engine.save_to_file(text, temp_path)
                
                # Use a simple loop instead of runAndWait
                self.engine.startLoop(False)
                
                # Wait a reasonable amount of time
                import time
                start_time = time.time()
                while self.engine.isBusy() and (time.time() - start_time) < 5:
                    time.sleep(0.1)
                
                self.engine.endLoop()
                
            except Exception as e:
                # Fallback: try the original method with shorter timeout
                self.engine.save_to_file(text, temp_path)
                import threading
                
                def run_tts():
                    try:
                        self.engine.runAndWait()
                    except:
                        pass
                
                tts_thread = threading.Thread(target=run_tts)
                tts_thread.daemon = True
                tts_thread.start()
                tts_thread.join(timeout=5)  # 5 second timeout
            
            # Check if file was created and has content
            if not os.path.exists(temp_path):
                return {"success": False, "error": "Audio file was not created"}
            
            file_size = os.path.getsize(temp_path)
            if file_size == 0:
                return {"success": False, "error": "Audio file is empty"}
            
            # Read the generated audio file
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return {
                "success": True,
                "audio_data": audio_data,
                "text": text,
                "format": "wav",
                "file_size": file_size
            }
            
        except Exception as e:
            return {"success": False, "error": f"Simple TTS generation error: {str(e)}"}
    
    def generate_audio_file(self, text: str, use_voice_profile: bool = True) -> Dict[str, Any]:
        """Generate actual audio file from text."""
        
        try:
            if not self.engine:
                return {"success": False, "error": "TTS engine not available"}
            
            # Generate audio using pyttsx3 with timeout
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_path = temp_file.name
            
            # Configure voice based on profile if available - DO THIS RIGHT BEFORE GENERATION
            if use_voice_profile and self.voice_profile:
                print(f"🎤 Applying voice profile: {self.voice_profile['voice_quality']['voice_type']}")
                self._configure_voice_from_profile()
                
                # Verify settings were applied
                current_rate = self.engine.getProperty('rate')
                current_volume = self.engine.getProperty('volume')
                current_voice = self.engine.getProperty('voice')
                print(f"✅ Applied settings - Rate: {current_rate}, Volume: {current_volume}, Voice: {current_voice}")
            else:
                print("⚠️ No voice profile available, using default settings")
                self.engine.setProperty('rate', 150)
                self.engine.setProperty('volume', 0.8)
            
            # Save audio to file
            self.engine.save_to_file(text, temp_path)
            
            # Use a timeout to prevent hanging
            import threading
            import time
            
            def run_tts():
                self.engine.runAndWait()
            
            # Start TTS in a separate thread
            tts_thread = threading.Thread(target=run_tts)
            tts_thread.daemon = True
            tts_thread.start()
            
            # Wait for completion with timeout
            tts_thread.join(timeout=10)  # 10 second timeout
            
            if tts_thread.is_alive():
                return {"success": False, "error": "TTS generation timed out after 10 seconds"}
            
            # Check if file was created and has content
            if not os.path.exists(temp_path):
                return {"success": False, "error": "Audio file was not created"}
            
            file_size = os.path.getsize(temp_path)
            if file_size == 0:
                return {"success": False, "error": "Audio file is empty"}
            
            # Read the generated audio file
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return {
                "success": True,
                "audio_data": audio_data,
                "text": text,
                "format": "wav",
                "file_size": file_size
            }
            
        except Exception as e:
            return {"success": False, "error": f"TTS generation error: {str(e)}"}
    
    def generate_audio_gtts(self, text: str, use_voice_profile: bool = True) -> Dict[str, Any]:
        """Generate audio using Google Text-to-Speech."""
        
        try:
            # Configure voice parameters
            lang = 'en'
            slow = False
            
            if use_voice_profile and self.voice_profile:
                # Adjust parameters based on voice profile
                tempo = self.voice_profile["rhythm_characteristics"]["tempo"]
                base_pitch = self.voice_profile["pitch_characteristics"]["base_pitch"]
                voice_type = self.voice_profile["voice_quality"]["voice_type"]
                
                # Adjust speed based on tempo
                if tempo < 100:
                    slow = True
                
                # Note: Google TTS has limited voice customization options
                # We can only control speed (slow parameter) and language
                # For more voice matching, we'd need a service like Azure Speech or ElevenLabs
                print(f"Google TTS: tempo={tempo:.0f}BPM, pitch={base_pitch:.0f}Hz, type={voice_type}, slow={slow}")
            
            # Generate TTS
            tts = gTTS(text=text, lang=lang, slow=slow)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_path = temp_file.name
            
            tts.save(temp_path)
            
            # Check if file was created and has content
            if not os.path.exists(temp_path):
                return {"success": False, "error": "Google TTS audio file was not created"}
            
            file_size = os.path.getsize(temp_path)
            if file_size == 0:
                return {"success": False, "error": "Google TTS audio file is empty"}
            
            # Read the generated audio file
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return {
                "success": True,
                "audio_data": audio_data,
                "text": text,
                "format": "mp3",
                "file_size": file_size
            }
            
        except Exception as e:
            return {"success": False, "error": f"Google TTS error: {str(e)}"}
    
    def _configure_voice_from_profile(self):
        """Configure TTS engine based on voice profile."""
        
        if not self.voice_profile or not self.engine:
            return
        
        try:
            # Get voice characteristics
            tempo = self.voice_profile["rhythm_characteristics"]["tempo"]
            base_pitch = self.voice_profile["pitch_characteristics"]["base_pitch"]
            clarity = self.voice_profile["voice_quality"]["clarity"]
            voice_type = self.voice_profile["voice_quality"]["voice_type"]
            emotional_tone = self.voice_profile["voice_quality"]["emotional_tone"]
            
            # Adjust speech rate based on tempo (normalize around 120 BPM)
            rate = int(150 * (tempo / 120))
            rate = max(50, min(300, rate))  # Clamp between 50 and 300
            self.engine.setProperty('rate', rate)
            
            # Adjust volume based on clarity
            volume = min(1.0, max(0.3, clarity))
            self.engine.setProperty('volume', volume)
            
            # Get available voices
            voices = self.engine.getProperty('voices')
            if voices:
                print(f"Available voices: {[v.name for v in voices]}")
                print(f"Analyzing: pitch={base_pitch:.0f}Hz, tempo={tempo:.0f}BPM, type={voice_type}, tone={emotional_tone}")
                
                # More sophisticated voice selection based on analyzed characteristics
                selected_voice = None
                voice_scores = []
                
                for voice in voices:
                    score = 0
                    voice_name_lower = voice.name.lower()
                    
                    # Pitch-based scoring
                    if base_pitch > 180:  # High pitch - prefer female voices
                        if any(female_indicator in voice_name_lower for female_indicator in 
                               ['female', 'zira', 'susan', 'hazel', 'catherine', 'linda', 'karen', 'sarah', 'emma']):
                            score += 10
                    elif base_pitch < 120:  # Low pitch - prefer male voices
                        if any(male_indicator in voice_name_lower for male_indicator in 
                               ['male', 'david', 'mark', 'richard', 'james', 'michael', 'daniel', 'john', 'paul']):
                            score += 10
                    else:  # Medium pitch - neutral preference
                        score += 5
                    
                    # Voice type matching
                    if 'bright' in voice_type:
                        if any(bright_indicator in voice_name_lower for bright_indicator in 
                               ['zira', 'susan', 'mark', 'david', 'bright', 'clear']):
                            score += 5
                    elif 'warm' in voice_type:
                        if any(warm_indicator in voice_name_lower for warm_indicator in 
                               ['hazel', 'catherine', 'richard', 'james', 'warm', 'soft']):
                            score += 5
                    
                    # Emotional tone matching
                    if 'excited' in emotional_tone or 'happy' in emotional_tone:
                        if any(energetic_indicator in voice_name_lower for energetic_indicator in 
                               ['zira', 'susan', 'mark', 'david', 'energetic', 'cheerful']):
                            score += 3
                    elif 'sad' in emotional_tone or 'calm' in emotional_tone:
                        if any(calm_indicator in voice_name_lower for calm_indicator in 
                               ['hazel', 'catherine', 'richard', 'james', 'calm', 'soft', 'gentle']):
                            score += 3
                    
                    voice_scores.append((voice, score))
                
                # Sort by score and select the best match
                voice_scores.sort(key=lambda x: x[1], reverse=True)
                if voice_scores and voice_scores[0][1] > 0:
                    selected_voice = voice_scores[0][0]
                    print(f"Voice scores: {[(v.name, s) for v, s in voice_scores[:3]]}")
                else:
                    # Fallback to first available voice
                    selected_voice = voices[0] if voices else None
                    print("No voice matched criteria, using first available")
                
                # Apply the selected voice
                if selected_voice:
                    self.engine.setProperty('voice', selected_voice.id)
                    print(f"✅ Selected voice: {selected_voice.name} (score: {voice_scores[0][1] if voice_scores else 'N/A'})")
                    print(f"   Applied settings: rate={rate}, volume={volume:.2f}")
                else:
                    print("❌ No voice available")
            
        except Exception as e:
            print(f"Voice configuration error: {e}")
            # If voice configuration fails, continue with defaults
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices."""
        
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            return [{"id": voice.id, "name": voice.name} for voice in voices] if voices else []
        except:
            return []
    
    def clone_voice_elevenlabs(self, audio_data: bytes, voice_name: str = None) -> Dict[str, Any]:
        """Clone voice using ElevenLabs from uploaded audio data."""
        
        if not self.elevenlabs:
            return {
                "success": False,
                "error": "ElevenLabs not initialized. Please provide API key."
            }
        
        try:
            result = self.elevenlabs.clone_voice_from_audio(audio_data, voice_name)
            if result["success"]:
                print(f"🎤 Voice cloned successfully: {result['voice_name']} (ID: {result['voice_id']})")
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Voice cloning failed: {str(e)}"
            }
    
    def generate_speech_elevenlabs(self, text: str, voice_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate speech using ElevenLabs cloned voice."""
        
        if not self.elevenlabs:
            return {
                "success": False,
                "error": "ElevenLabs not initialized. Please provide API key."
            }
        
        try:
            result = self.elevenlabs.generate_speech(text, voice_settings)
            if result["success"]:
                print(f"🔊 ElevenLabs audio generated: {len(result['audio_data'])} bytes")
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"ElevenLabs speech generation failed: {str(e)}"
            }
    
    def get_elevenlabs_voice_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the cloned ElevenLabs voice."""
        
        if not self.elevenlabs:
            return None
        
        return self.elevenlabs.get_voice_info()
    
    def test_elevenlabs_connection(self) -> Dict[str, Any]:
        """Test ElevenLabs API connection."""
        
        if not self.elevenlabs:
            return {
                "success": False,
                "error": "ElevenLabs not initialized. Please provide API key."
            }
        
        return self.elevenlabs.test_connection()
    
    def delete_elevenlabs_voice(self) -> bool:
        """Delete the cloned ElevenLabs voice."""
        
        if not self.elevenlabs:
            return False
        
        return self.elevenlabs.delete_voice()
