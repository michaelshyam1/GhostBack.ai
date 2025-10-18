"""
Voice Analysis and Text-to-Speech for GhostBack.ai
Analyzes voice characteristics and generates matching speech
"""

import librosa
import numpy as np
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
import io
import base64
from scipy import stats
import tempfile
import os
from pydub import AudioSegment
import subprocess
import platform

class VoiceAnalyzer:
    """Analyzes voice characteristics from audio samples."""
    
    def __init__(self):
        self.voice_profile = {}
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable path."""
        try:
            # Try common paths
            if platform.system() == "Windows":
                # Check winget installation path
                winget_path = os.path.expanduser("~/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0-full_build/bin/ffmpeg.exe")
                if os.path.exists(winget_path):
                    return winget_path
                
                # Check if ffmpeg is in PATH
                result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True)
                if result.returncode == 0:
                    return "ffmpeg"
            
            # Try system PATH
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            if result.returncode == 0:
                return "ffmpeg"
                
        except Exception:
            pass
        
        return "ffmpeg"  # Fallback to system PATH
    
    def _convert_audio_format(self, audio_data: bytes, file_extension: str) -> bytes:
        """Convert audio data to WAV format for librosa processing."""
        
        # For M4A files, use direct FFmpeg conversion as pydub has issues
        if file_extension.lower() == 'm4a':
            return self._convert_with_ffmpeg_direct(audio_data, file_extension)
        
        try:
            # Set FFmpeg path for pydub - use absolute paths
            ffprobe_path = self.ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")
            
            # Configure pydub with absolute paths
            AudioSegment.converter = self.ffmpeg_path
            AudioSegment.ffmpeg = self.ffmpeg_path
            AudioSegment.ffprobe = ffprobe_path
            
            # Test FFmpeg accessibility
            try:
                test_result = subprocess.run([self.ffmpeg_path, "-version"], 
                                          capture_output=True, text=True, timeout=5)
                if test_result.returncode != 0:
                    raise Exception("FFmpeg test failed")
            except Exception as ffmpeg_test_error:
                raise Exception(f"FFmpeg not accessible: {str(ffmpeg_test_error)}")
            
            # Create AudioSegment from bytes
            if file_extension.lower() == 'mp3':
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            elif file_extension.lower() == 'wav':
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="wav")
            else:
                # Try to auto-detect format
                audio = AudioSegment.from_file(io.BytesIO(audio_data))
            
            # Convert to WAV format
            wav_data = io.BytesIO()
            audio.export(wav_data, format="wav")
            wav_data.seek(0)
            
            return wav_data.read()
            
        except Exception as e:
            error_msg = str(e)
            if "Format not recognised" in error_msg or "FFmpeg" in error_msg:
                return self._convert_with_ffmpeg_direct(audio_data, file_extension)
            else:
                raise Exception(f"Failed to convert {file_extension.upper()} to WAV: {error_msg}")
    
    def _convert_with_ffmpeg_direct(self, audio_data: bytes, file_extension: str) -> bytes:
        """Convert audio using FFmpeg directly when pydub fails."""
        
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as input_file:
                input_file.write(audio_data)
                input_file.flush()
                input_path = input_file.name
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
                output_path = output_file.name
            
            try:
                # Use FFmpeg directly to convert
                cmd = [
                    self.ffmpeg_path,
                    "-i", input_path,
                    "-acodec", "pcm_s16le",
                    "-ar", "22050",
                    "-ac", "1",
                    "-y",  # Overwrite output file
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    # Check for common error patterns and provide helpful messages
                    stderr = result.stderr.lower()
                    if "invalid data found" in stderr or "moov atom not found" in stderr:
                        raise Exception("The M4A file appears to be corrupted or incomplete. Please try a different file or convert it to WAV/MP3 format.")
                    elif "no such file" in stderr:
                        raise Exception("FFmpeg could not find the input file. Please try again.")
                    else:
                        raise Exception(f"FFmpeg conversion failed: {result.stderr}")
                
                # Read the converted WAV file
                with open(output_path, "rb") as f:
                    wav_data = f.read()
                
                return wav_data
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(input_path)
                    os.unlink(output_path)
                except:
                    pass
                    
        except Exception as e:
            raise Exception(f"Direct FFmpeg conversion failed: {str(e)}")
    
    def _fallback_audio_processing(self, audio_data: bytes, file_extension: str) -> bytes:
        """Fallback audio processing when FFmpeg is not available."""
        
        # For M4A files, try to use librosa directly with different parameters
        if file_extension.lower() == 'm4a':
            try:
                # Try loading with librosa directly (sometimes works for M4A)
                y, sr = librosa.load(io.BytesIO(audio_data), sr=None)
                
                # Convert back to WAV format using librosa
                import soundfile as sf
                wav_data = io.BytesIO()
                sf.write(wav_data, y, sr, format='WAV')
                wav_data.seek(0)
                
                return wav_data.read()
                
            except Exception as librosa_error:
                # Provide helpful installation instructions
                error_msg = f"""M4A processing failed. The file may be corrupted or in an unsupported format.

Troubleshooting steps:
1. **Try a different M4A file** - The current file may be corrupted
2. **Convert to WAV/MP3** - Use an online converter or audio software
3. **Check file format** - Ensure it's a valid M4A audio file
4. **File size** - Very large files may cause issues

If the problem persists, please try uploading a WAV or MP3 file instead.

Error details: {str(librosa_error)}"""
                raise Exception(error_msg)
        else:
            raise Exception(f"Audio conversion failed for {file_extension.upper()}. FFmpeg may not be installed.")
    
    def analyze_voice_sample(self, audio_data: bytes, sample_rate: int = 22050, file_extension: str = None) -> Dict[str, Any]:
        """Analyze voice characteristics from audio data."""
        
        try:
            # If file extension is provided and it's not WAV, convert it first
            if file_extension and file_extension.lower() != 'wav':
                try:
                    audio_data = self._convert_audio_format(audio_data, file_extension)
                except Exception as conv_error:
                    return {
                        "success": False,
                        "error": f"Audio conversion failed: {str(conv_error)}",
                        "features": {}
                    }
            
            # Load audio with format detection
            y, sr = librosa.load(io.BytesIO(audio_data), sr=sample_rate)
            
            # Extract features
            features = self._extract_voice_features(y, sr)
            
            return {
                "success": True,
                "features": features,
                "sample_rate": sr,
                "duration": len(y) / sr
            }
            
        except Exception as e:
            # Try with different sample rate if first attempt fails
            try:
                y, sr = librosa.load(io.BytesIO(audio_data), sr=None)  # Use original sample rate
                features = self._extract_voice_features(y, sr)
                
                return {
                    "success": True,
                    "features": features,
                    "sample_rate": sr,
                    "duration": len(y) / sr
                }
            except Exception as e2:
                return {
                    "success": False,
                    "error": f"Failed to load audio: {str(e)}. Secondary error: {str(e2)}",
                    "features": {}
                }
    
    def _extract_voice_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract comprehensive voice features."""
        
        # Fundamental frequency (pitch)
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        f0_clean = f0[~np.isnan(f0)]
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        
        # MFCC features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Rhythm features
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo)  # Convert to scalar
        
        # Voice quality features
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        
        # Energy features
        rms = librosa.feature.rms(y=y)[0]
        
        # Calculate statistics
        features = {
            # Pitch characteristics
            "mean_pitch": np.mean(f0_clean) if len(f0_clean) > 0 else 0,
            "pitch_std": np.std(f0_clean) if len(f0_clean) > 0 else 0,
            "pitch_range": np.ptp(f0_clean) if len(f0_clean) > 0 else 0,
            "pitch_median": np.median(f0_clean) if len(f0_clean) > 0 else 0,
            
            # Spectral characteristics
            "mean_spectral_centroid": np.mean(spectral_centroids),
            "spectral_centroid_std": np.std(spectral_centroids),
            "mean_spectral_rolloff": np.mean(spectral_rolloff),
            "mean_spectral_bandwidth": np.mean(spectral_bandwidth),
            
            # Voice quality
            "mean_zero_crossing_rate": np.mean(zero_crossing_rate),
            "zero_crossing_rate_std": np.std(zero_crossing_rate),
            
            # Energy characteristics
            "mean_rms": np.mean(rms),
            "rms_std": np.std(rms),
            "dynamic_range": np.ptp(rms),
            
            # Rhythm
            "tempo": tempo,
            
            # MFCC characteristics (first few coefficients)
            "mfcc_mean": np.mean(mfccs, axis=1).tolist()[:5],  # First 5 MFCCs
            "mfcc_std": np.std(mfccs, axis=1).tolist()[:5],
            
            # Voice type classification
            "voice_type": self._classify_voice_type(f0_clean, spectral_centroids, rms),
            "emotional_tone": self._analyze_emotional_tone(f0_clean, spectral_centroids, rms, zero_crossing_rate)
        }
        
        return features
    
    def _classify_voice_type(self, f0: np.ndarray, spectral_centroids: np.ndarray, rms: np.ndarray) -> str:
        """Classify voice type based on characteristics."""
        
        if len(f0) == 0:
            return "unknown"
        
        mean_pitch = np.mean(f0)
        mean_spectral_centroid = np.mean(spectral_centroids)
        mean_energy = np.mean(rms)
        
        # Simple classification based on pitch and spectral characteristics
        if mean_pitch > 200:  # High pitch
            if mean_spectral_centroid > 2000:
                return "bright_high"
            else:
                return "warm_high"
        elif mean_pitch > 120:  # Medium pitch
            if mean_spectral_centroid > 1800:
                return "bright_medium"
            else:
                return "warm_medium"
        else:  # Low pitch
            if mean_spectral_centroid > 1500:
                return "bright_low"
            else:
                return "warm_low"
    
    def _analyze_emotional_tone(self, f0: np.ndarray, spectral_centroids: np.ndarray, 
                               rms: np.ndarray, zero_crossing_rate: np.ndarray) -> str:
        """Analyze emotional tone from voice characteristics."""
        
        if len(f0) == 0:
            return "neutral"
        
        # Calculate features
        pitch_variation = np.std(f0) / (np.mean(f0) + 1e-6)
        energy_variation = np.std(rms) / (np.mean(rms) + 1e-6)
        mean_spectral_centroid = np.mean(spectral_centroids)
        mean_zcr = np.mean(zero_crossing_rate)
        
        # Emotional classification based on voice characteristics
        if pitch_variation > 0.3 and energy_variation > 0.4:
            return "excited_animated"
        elif pitch_variation > 0.2 and mean_spectral_centroid > 2000:
            return "cheerful_bright"
        elif pitch_variation < 0.1 and mean_spectral_centroid < 1500:
            return "calm_serene"
        elif mean_zcr > 0.1 and energy_variation > 0.3:
            return "energetic_lively"
        elif pitch_variation < 0.15 and mean_spectral_centroid < 1800:
            return "warm_gentle"
        else:
            return "neutral_balanced"
    
    def create_voice_profile(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Create a voice profile for text-to-speech generation."""
        
        return {
            "pitch_characteristics": {
                "base_pitch": float(features.get("mean_pitch", 150)),
                "pitch_variation": float(features.get("pitch_std", 20)),
                "pitch_range": float(features.get("pitch_range", 100))
            },
            "spectral_characteristics": {
                "brightness": float(features.get("mean_spectral_centroid", 2000)),
                "warmth": float(1.0 - (features.get("mean_spectral_centroid", 2000) / 4000)),
                "clarity": float(features.get("mean_spectral_bandwidth", 1000))
            },
            "rhythm_characteristics": {
                "tempo": float(features.get("tempo", 120)),
                "energy_variation": float(features.get("rms_std", 0.1)),
                "dynamic_range": float(features.get("dynamic_range", 0.5))
            },
            "voice_quality": {
                "voice_type": features.get("voice_type", "warm_medium"),
                "emotional_tone": features.get("emotional_tone", "neutral_balanced"),
                "clarity": float(1.0 - features.get("mean_zero_crossing_rate", 0.05))
            }
        }


class TextToSpeechGenerator:
    """Generates speech that matches analyzed voice characteristics."""
    
    def __init__(self):
        self.voice_profile = None
    
    def set_voice_profile(self, profile: Dict[str, Any]):
        """Set the voice profile for speech generation."""
        self.voice_profile = profile
    
    def generate_speech_parameters(self, text: str) -> Dict[str, Any]:
        """Generate speech parameters based on voice profile and text content."""
        
        if not self.voice_profile:
            return self._default_parameters()
        
        # Analyze text for emotional content
        text_emotion = self._analyze_text_emotion(text)
        
        # Get base characteristics
        pitch_base = self.voice_profile["pitch_characteristics"]["base_pitch"]
        pitch_variation = self.voice_profile["pitch_characteristics"]["pitch_variation"]
        brightness = self.voice_profile["spectral_characteristics"]["brightness"]
        tempo = self.voice_profile["rhythm_characteristics"]["tempo"]
        
        # Adjust parameters based on text emotion
        emotion_multipliers = {
            "excited": {"pitch": 1.2, "tempo": 1.3, "energy": 1.4},
            "sad": {"pitch": 0.8, "tempo": 0.7, "energy": 0.6},
            "angry": {"pitch": 1.1, "tempo": 1.1, "energy": 1.3},
            "calm": {"pitch": 0.9, "tempo": 0.8, "energy": 0.7},
            "happy": {"pitch": 1.1, "tempo": 1.2, "energy": 1.2},
            "neutral": {"pitch": 1.0, "tempo": 1.0, "energy": 1.0}
        }
        
        multiplier = emotion_multipliers.get(text_emotion, emotion_multipliers["neutral"])
        
        return {
            "pitch": pitch_base * multiplier["pitch"],
            "pitch_variation": pitch_variation * multiplier["pitch"],
            "tempo": tempo * multiplier["tempo"],
            "energy": multiplier["energy"],
            "brightness": brightness,
            "voice_type": self.voice_profile["voice_quality"]["voice_type"],
            "emotional_tone": text_emotion
        }
    
    def _analyze_text_emotion(self, text: str) -> str:
        """Analyze text for emotional content."""
        
        text_lower = text.lower()
        
        # Simple emotion detection based on keywords
        excited_words = ["!", "amazing", "wow", "excited", "great", "fantastic", "awesome"]
        sad_words = ["sad", "depressed", "down", "crying", "hurt", "pain", "sorrow"]
        angry_words = ["angry", "mad", "furious", "hate", "rage", "annoyed", "frustrated"]
        happy_words = ["happy", "joy", "smile", "laugh", "fun", "good", "nice", "love"]
        calm_words = ["calm", "peaceful", "relaxed", "quiet", "serene", "gentle"]
        
        if any(word in text_lower for word in excited_words):
            return "excited"
        elif any(word in text_lower for word in sad_words):
            return "sad"
        elif any(word in text_lower for word in angry_words):
            return "angry"
        elif any(word in text_lower for word in happy_words):
            return "happy"
        elif any(word in text_lower for word in calm_words):
            return "calm"
        else:
            return "neutral"
    
    def _default_parameters(self) -> Dict[str, Any]:
        """Default speech parameters when no voice profile is available."""
        return {
            "pitch": 150,
            "pitch_variation": 20,
            "tempo": 120,
            "energy": 1.0,
            "brightness": 2000,
            "voice_type": "warm_medium",
            "emotional_tone": "neutral"
        }
    
    def generate_voice_description(self, parameters: Dict[str, Any]) -> str:
        """Generate a human-readable description of the voice characteristics."""
        
        voice_type = parameters.get("voice_type", "warm_medium")
        emotional_tone = parameters.get("emotional_tone", "neutral")
        pitch = parameters.get("pitch", 150)
        tempo = parameters.get("tempo", 120)
        
        # Voice type descriptions
        voice_descriptions = {
            "bright_high": "bright and high-pitched",
            "warm_high": "warm and high-pitched", 
            "bright_medium": "bright and medium-pitched",
            "warm_medium": "warm and medium-pitched",
            "bright_low": "bright and low-pitched",
            "warm_low": "warm and low-pitched"
        }
        
        # Tempo descriptions
        if tempo > 140:
            tempo_desc = "fast-paced"
        elif tempo > 100:
            tempo_desc = "moderate-paced"
        else:
            tempo_desc = "slow-paced"
        
        # Emotional tone descriptions
        emotion_descriptions = {
            "excited_animated": "excited and animated",
            "cheerful_bright": "cheerful and bright",
            "calm_serene": "calm and serene",
            "energetic_lively": "energetic and lively",
            "warm_gentle": "warm and gentle",
            "neutral_balanced": "neutral and balanced"
        }
        
        voice_desc = voice_descriptions.get(voice_type, "medium-pitched")
        emotion_desc = emotion_descriptions.get(emotional_tone, "balanced")
        
        return f"A {voice_desc} voice with {emotion_desc} characteristics, speaking at a {tempo_desc} tempo."
