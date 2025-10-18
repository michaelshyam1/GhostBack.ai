"""
ElevenLabs Voice Cloning Page for GhostBack.ai
Handles voice cloning and TTS generation using ElevenLabs API
"""

import streamlit as st
import os
from tts_integration import TTSIntegration

st.set_page_config(page_title="Voice Cloning", page_icon="🎭")

st.title("🎭 ElevenLabs Voice Cloning")
st.write("Upload your voice sample to create a personalized AI voice using ElevenLabs.")

# Initialize TTS integration with ElevenLabs
if 'tts_integration' not in st.session_state:
    # Get API key from environment or user input
    elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
    if not elevenlabs_key:
        # Use the provided API key
        elevenlabs_key = "sk_56f052abde4435779cd252bf82654fb333801488dacf9f75"
        st.success("✅ Using provided ElevenLabs API key")
    else:
        st.success("✅ ElevenLabs API key loaded from environment")
    
    if elevenlabs_key:
        st.session_state.tts_integration = TTSIntegration(elevenlabs_api_key=elevenlabs_key)
    else:
        st.session_state.tts_integration = TTSIntegration()

# Test connection
if st.button("🔍 Test ElevenLabs Connection", key="test_elevenlabs"):
    with st.spinner("Testing connection..."):
        result = st.session_state.tts_integration.test_elevenlabs_connection()
        
        if result["success"]:
            st.success(f"✅ {result['message']}")
            if 'character_count' in result:
                st.write(f"**Character Usage:** {result['character_count']:,} / {result['character_limit']:,}")
        else:
            st.error(f"❌ {result['error']}")
            
            # Check for specific error types
            if "quota_exceeded" in result['error'] or "credits" in result['error']:
                st.error("🚫 **No Credits Remaining**")
                st.write("Your ElevenLabs API key has **0 credits remaining**.")
                st.write("This appears to be a hackathon/free tier key that can't be used for voice cloning.")
                
                st.info("**💳 To use voice cloning, you need:**")
                st.write("1. **Go to [ElevenLabs.io](https://elevenlabs.io)**")
                st.write("2. **Sign up for a paid plan** (Starter plan: $5/month)")
                st.write("3. **Get a new API key** with credits")
                st.write("4. **Replace the key** in this app")
                
                st.code("""
# Replace this line in pages/3_🎭_Voice_Cloning.py (line 21):
elevenlabs_key = "YOUR_NEW_PAID_API_KEY_HERE"
                """, language="python")
                
                st.success("✅ **Good news**: The integration is working perfectly! You just need credits.")
                
            elif "missing_permissions" in result['error']:
                st.error("🚫 **Missing Permissions**")
                st.write("Your API key is missing the `voices_write` permission required for voice cloning.")
                st.write("**This usually means:**")
                st.write("1. **Free/Hackathon account** - Voice cloning requires a paid plan")
                st.write("2. **Limited API key** - Your key doesn't have full permissions")
                st.write("3. **Account restrictions** - Your account may have limitations")
                
                st.info("**💳 To fix this:**")
                st.write("1. **Upgrade to a paid ElevenLabs plan** (Starter: $5/month)")
                st.write("2. **Get a new API key** with full permissions")
                st.write("3. **Contact ElevenLabs support** if you have a paid account")
                
                st.success("✅ **Good news**: The integration is working! You just need the right permissions.")
                
            elif "invalid_content" in result['error'] or "corrupted" in result['error']:
                st.error("🚫 **Audio File Issue**")
                st.write("The uploaded audio file appears to be corrupted or in an unsupported format.")
                st.write("**Please try:**")
                st.write("1. **Use a different M4A file** - The current one may be corrupted")
                st.write("2. **Convert to WAV/MP3** - Use an online converter or audio software")
                st.write("3. **Check file size** - Very large files may cause issues")
                st.write("4. **Ensure clear audio** - Background noise can cause problems")
                
                st.info("💡 **Tip**: Try recording a short, clear voice sample (10-30 seconds) in a quiet environment.")

# Voice cloning section
st.subheader("🎤 Clone Your Voice")

# Check if we have a working ElevenLabs connection
has_working_elevenlabs = st.session_state.tts_integration.elevenlabs is not None

if not has_working_elevenlabs:
    st.warning("⚠️ **ElevenLabs not available** - Voice cloning requires a valid API key with credits.")
    st.info("💡 **Demo Mode**: You can still upload and analyze voice samples using the local voice analysis.")
else:
    # Check if we have credits
    st.info("🔍 **ElevenLabs Connected** - Click 'Test Connection' above to check your credit status.")

# File upload
uploaded_file = st.file_uploader(
    "Upload your voice sample (M4A, MP3, WAV):",
    type=['m4a', 'mp3', 'wav'],
    help="Upload a clear voice sample (10-60 seconds recommended)"
)

if uploaded_file is not None:
    # Show uploaded audio
    st.audio(uploaded_file, format='audio/wav')
    
    # Voice name input
    voice_name = st.text_input(
        "Voice Name:",
        value=f"My_Voice_{uploaded_file.name.split('.')[0]}",
        help="Choose a name for your cloned voice"
    )
    
    # Clone voice button
    if st.button("🎭 Clone Voice", key="clone_voice"):
        if not st.session_state.tts_integration.elevenlabs:
            st.error("❌ ElevenLabs not available. Please get a valid API key with credits.")
        else:
            # Validate file before cloning
            file_size = len(uploaded_file.getvalue())
            if file_size == 0:
                st.error("❌ The uploaded file is empty. Please try a different file.")
            elif file_size > 50 * 1024 * 1024:  # 50MB limit
                st.error("❌ File too large. Please use a file smaller than 50MB.")
            else:
                with st.spinner("Cloning voice... This may take a few minutes."):
                    # Read audio data
                    audio_data = uploaded_file.read()
                    
                    # Show file info
                    st.info(f"📁 File size: {file_size:,} bytes")
                    
                    # Clone voice
                    result = st.session_state.tts_integration.clone_voice_elevenlabs(
                        audio_data, voice_name
                    )
                    
                    if result["success"]:
                        st.success(f"✅ {result['message']}")
                        st.session_state.voice_cloned = True
                        st.session_state.cloned_voice_id = result["voice_id"]
                        st.session_state.cloned_voice_name = result["voice_name"]
                    else:
                        st.error(f"❌ {result['error']}")
    
    # Voice analysis using local tools (always available)
    st.subheader("🔍 Voice Analysis (Local)")
    st.write("**This works even without ElevenLabs credits!**")
    
    if st.button("🔍 Analyze Voice Characteristics", key="analyze_voice_local"):
        with st.spinner("Analyzing voice characteristics..."):
                # Read audio data
                audio_data = uploaded_file.read()
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                # Analyze using local voice analyzer
                analysis_result = st.session_state.tts_integration.voice_analyzer.analyze_voice_sample(
                    audio_data, file_extension=file_extension
                )
                
                if analysis_result["success"]:
                    st.success("✅ Voice analysis complete!")
                    
                    # Display analysis results
                    features = analysis_result["features"]
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Mean Pitch", f"{features['mean_pitch']:.0f} Hz")
                        st.metric("Tempo", f"{features['tempo']:.0f} BPM")
                        st.metric("Voice Type", features['voice_type'].replace('_', ' ').title())
                    
                    with col2:
                        st.metric("Emotional Tone", features['emotional_tone'].replace('_', ' ').title())
                        st.metric("Clarity", f"{features['mean_zero_crossing_rate']:.3f}")
                        st.metric("Energy", f"{features.get('energy', features.get('mean_rms', 0)):.2f}")
                    
                    # Create voice profile
                    voice_profile = st.session_state.tts_integration.voice_analyzer.create_voice_profile(features)
                    st.session_state.voice_profile = voice_profile
                    
                    st.success("✅ Voice profile created! You can use this with local TTS engines.")
                else:
                    st.error(f"❌ Analysis failed: {analysis_result['error']}")

# Show cloned voice info
if st.session_state.get('voice_cloned', False):
    st.subheader("🎯 Cloned Voice Information")
    
    voice_info = st.session_state.tts_integration.get_elevenlabs_voice_info()
    if voice_info and 'error' not in voice_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Voice Name:** {voice_info['name']}")
            st.write(f"**Voice ID:** {voice_info['voice_id']}")
            st.write(f"**Category:** {voice_info['category']}")
        
        with col2:
            st.write(f"**Description:** {voice_info['description']}")
            st.write(f"**Stability:** {voice_info['settings']['stability']}")
            st.write(f"**Similarity Boost:** {voice_info['settings']['similarity_boost']}")
    else:
        st.warning("Could not retrieve voice information")

# TTS generation section
if st.session_state.get('voice_cloned', False):
    st.subheader("🔊 Generate Speech")
    
    # Text input
    text_input = st.text_area(
        "Enter text to generate speech:",
        value="Hello! This is my cloned voice speaking. How do I sound?",
        height=100
    )
    
    # Voice settings
    with st.expander("🎛️ Voice Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            stability = st.slider(
                "Stability",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                help="Lower values make voice more variable and expressive"
            )
            similarity_boost = st.slider(
                "Similarity Boost",
                min_value=0.0,
                max_value=1.0,
                value=0.75,
                help="Higher values make voice more similar to original"
            )
        
        with col2:
            style = st.slider(
                "Style",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                help="Style exaggeration (0.0 = normal, 1.0 = very exaggerated)"
            )
            use_speaker_boost = st.checkbox(
                "Use Speaker Boost",
                value=True,
                help="Enhance voice similarity"
            )
    
    # Generate speech
    if st.button("🔊 Generate Speech", key="generate_speech"):
        if not text_input.strip():
            st.warning("Please enter some text to generate speech.")
        else:
            with st.spinner("Generating speech with your cloned voice..."):
                voice_settings = {
                    'stability': stability,
                    'similarity_boost': similarity_boost,
                    'style': style,
                    'use_speaker_boost': use_speaker_boost
                }
                
                result = st.session_state.tts_integration.generate_speech_elevenlabs(
                    text_input, voice_settings
                )
                
                if result["success"]:
                    st.audio(result["audio_data"], format="audio/mp3")
                    st.success("✅ Speech generated successfully!")
                    st.write(f"**Audio Size:** {result['file_size']:,} bytes")
                    st.write(f"**Voice:** {result['voice_name']}")
                else:
                    st.error(f"❌ {result['error']}")

# Voice management
if st.session_state.get('voice_cloned', False):
    st.subheader("🗑️ Voice Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Delete Cloned Voice", key="delete_voice"):
            if st.session_state.tts_integration.delete_elevenlabs_voice():
                st.success("✅ Voice deleted successfully!")
                st.session_state.voice_cloned = False
                st.session_state.cloned_voice_id = None
                st.session_state.cloned_voice_name = None
                st.rerun()
            else:
                st.error("❌ Failed to delete voice")
    
    with col2:
        if st.button("🔄 Refresh Voice Info", key="refresh_voice"):
            st.rerun()

# Footer
st.markdown("---")
st.markdown("### 🎯 How it works:")
st.markdown("""
1. **Upload Voice Sample** - Upload a clear M4A, MP3, or WAV file (10-60 seconds recommended)
2. **Clone Voice** - ElevenLabs analyzes your voice and creates a unique voice model
3. **Generate Speech** - Use your cloned voice to generate speech from any text
4. **Customize Settings** - Adjust stability, similarity, and style to fine-tune the voice
""")

st.markdown("### 💡 Tips for Best Results:")
st.markdown("""
- **Clear Audio**: Use a quiet environment with minimal background noise
- **Consistent Speech**: Speak at a normal pace and volume
- **Good Quality**: Use a decent microphone if possible
- **Length**: 10-60 seconds of speech works best
- **Content**: Speak naturally, as if talking to a friend
""")

st.markdown("### 🔧 Supported Formats:")
st.markdown("""
- **M4A** - Apple audio format (requires FFmpeg)
- **MP3** - Standard compressed audio
- **WAV** - Uncompressed audio (best quality)
""")
