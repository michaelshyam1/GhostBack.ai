"""
Voice Analysis and TTS Demo Page
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from tts_integration import TTSIntegration
from voice_analyzer import VoiceAnalyzer

# Page configuration
st.set_page_config(
    page_title="Voice Demo - GhostBack.ai",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 Voice Analysis & Text-to-Speech Demo")
st.markdown("Upload a voice sample to analyze characteristics and generate matching speech parameters.")

# Initialize components
if 'tts_integration' not in st.session_state:
    st.session_state.tts_integration = TTSIntegration()

if 'voice_analyzer' not in st.session_state:
    st.session_state.voice_analyzer = VoiceAnalyzer()

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload Voice Sample")
    
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['wav', 'mp3', 'm4a'],
        help="Upload a voice sample to analyze speaking characteristics. Note: M4A files require FFmpeg."
    )
    
    # Show M4A requirements info
    with st.expander("ℹ️ M4A File Requirements"):
        st.write("**M4A files require FFmpeg to be installed.**")
        st.write("If you get errors with M4A files:")
        st.write("1. Install FFmpeg: `choco install ffmpeg` (Windows)")
        st.write("2. Convert to WAV/MP3 instead")
        st.write("3. Use online converters")
    
    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/wav')
        
        # Analyze voice
        with st.spinner("Analyzing voice characteristics..."):
            result = st.session_state.tts_integration.process_voice_sample(uploaded_file)
            
            if result["success"]:
                file_format = result.get('file_format', 'unknown').upper()
                st.success(f"✅ Voice analysis complete! (Format: {file_format})")
                
                # Display voice profile
                profile = st.session_state.tts_integration.get_voice_profile_summary()
                if profile:
                    st.subheader("🎯 Voice Profile")
                    
                    # Voice characteristics
                    st.metric("Voice Type", profile['voice_type'].replace('_', ' ').title())
                    st.metric("Emotional Tone", profile['emotional_tone'].replace('_', ' ').title())
                    st.metric("Base Pitch", f"{profile['base_pitch']:.0f} Hz")
                    st.metric("Tempo", f"{profile['tempo']:.0f} BPM")
                    st.metric("Clarity", f"{profile['clarity']:.2f}")
                    st.metric("File Format", file_format)
                    
                    # Store for TTS generation
                    st.session_state.voice_analyzed = True
            else:
                st.error(f"❌ Analysis failed: {result['error']}")

with col2:
    st.subheader("🔊 Text-to-Speech Generation")
    
    # Debug section
    with st.expander("🔧 Debug TTS Engine"):
        st.write("**TTS Engine Status:**")
        if st.session_state.tts_integration.engine:
            st.success("✅ Local TTS engine available")
            voices = st.session_state.tts_integration.get_available_voices()
            st.write(f"Available voices: {len(voices)}")
            for voice in voices:
                st.write(f"- {voice['name']}")
        else:
            st.error("❌ Local TTS engine not available")
        
        # Test button
        if st.button("🧪 Test Basic TTS", key="test_basic_tts"):
            st.write("Testing basic TTS...")
            try:
                result = st.session_state.tts_integration.generate_audio_simple("Hello, this is a test.")
                if result["success"]:
                    st.audio(result["audio_data"], format="audio/wav")
                    st.success("✅ Basic TTS test successful!")
                else:
                    st.error(f"❌ Basic TTS test failed: {result['error']}")
            except Exception as e:
                st.error(f"❌ Test error: {str(e)}")
        
        # Show current TTS settings
        if st.button("🔍 Show Current TTS Settings", key="show_tts_settings"):
            if st.session_state.tts_integration.engine:
                rate = st.session_state.tts_integration.engine.getProperty('rate')
                volume = st.session_state.tts_integration.engine.getProperty('volume')
                voice = st.session_state.tts_integration.engine.getProperty('voice')
                
                st.write("**Current TTS Settings:**")
                st.write(f"- Rate: {rate}")
                st.write(f"- Volume: {volume}")
                st.write(f"- Voice: {voice}")
                
                if st.session_state.tts_integration.voice_profile:
                    st.write("**Voice Profile:**")
                    profile = st.session_state.tts_integration.voice_profile
                    st.write(f"- Voice Type: {profile['voice_quality']['voice_type']}")
                    st.write(f"- Base Pitch: {profile['pitch_characteristics']['base_pitch']:.0f} Hz")
                    st.write(f"- Tempo: {profile['rhythm_characteristics']['tempo']:.0f} BPM")
            else:
                st.error("TTS engine not available")
        
        # Force apply voice profile
        if st.button("🔄 Force Apply Voice Profile", key="force_apply_profile"):
            if st.session_state.tts_integration.voice_profile and st.session_state.tts_integration.engine:
                st.write("🔄 Applying voice profile...")
                st.session_state.tts_integration._configure_voice_from_profile()
                
                # Show updated settings
                rate = st.session_state.tts_integration.engine.getProperty('rate')
                volume = st.session_state.tts_integration.engine.getProperty('volume')
                voice = st.session_state.tts_integration.engine.getProperty('voice')
                
                st.success("✅ Voice profile applied!")
                st.write(f"**Updated Settings:** Rate: {rate}, Volume: {volume}, Voice: {voice}")
            else:
                st.error("No voice profile or TTS engine available")
    
    if st.session_state.get('voice_analyzed', False):
        # Text input for TTS
        text_input = st.text_area(
            "Enter text to generate speech parameters:",
            value="Hello, how are you doing today?",
            height=100
        )
        
        # Show voice profile information
        if st.session_state.tts_integration.voice_profile:
            st.subheader("🎤 Voice Profile Applied")
            profile = st.session_state.tts_integration.voice_profile
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.write(f"**Voice Type:** {profile['voice_quality']['voice_type']}")
                st.write(f"**Base Pitch:** {profile['pitch_characteristics']['base_pitch']:.0f} Hz")
                st.write(f"**Tempo:** {profile['rhythm_characteristics']['tempo']:.0f} BPM")
            
            with col_info2:
                st.write(f"**Emotional Tone:** {profile['voice_quality']['emotional_tone']}")
                st.write(f"**Clarity:** {profile['voice_quality']['clarity']:.2f}")
                st.write(f"**Brightness:** {profile['spectral_characteristics']['brightness']:.0f}")
        
        # Audio generation buttons - ALWAYS VISIBLE
        st.subheader("🔊 Generate Audio")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔊 Local TTS", key="demo_local_audio"):
                st.write("🔄 Generating local audio...")
                try:
                    # Try simple method first
                    audio_result = st.session_state.tts_integration.generate_audio_simple(text_input)
                    
                    if not audio_result["success"]:
                        # Fallback to original method
                        st.write("⚠️ Trying alternative method...")
                        audio_result = st.session_state.tts_integration.generate_audio_file(text_input)
                    
                    if audio_result["success"]:
                        st.audio(audio_result["audio_data"], format="audio/wav")
                        st.success("✅ Local audio generated!")
                        st.write(f"📊 Audio size: {len(audio_result['audio_data'])} bytes")
                    else:
                        st.error(f"❌ Local TTS failed: {audio_result['error']}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with col2:
            if st.button("🌐 Google TTS", key="demo_google_audio"):
                st.write("🔄 Generating Google TTS audio...")
                try:
                    audio_result = st.session_state.tts_integration.generate_audio_gtts(text_input)
                    
                    if audio_result["success"]:
                        st.audio(audio_result["audio_data"], format="audio/mp3")
                        st.success("✅ Google TTS audio generated!")
                        st.write(f"📊 Audio size: {len(audio_result['audio_data'])} bytes")
                    else:
                        st.error(f"❌ Google TTS failed: {audio_result['error']}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Speech parameters generation (optional)
        if st.button("Generate Speech Parameters"):
            with st.spinner("Generating speech parameters..."):
                tts_result = st.session_state.tts_integration.generate_speech_for_message(text_input)
                
                if tts_result["success"]:
                    st.success("✅ Speech parameters generated!")
                    
                    # Display parameters
                    parameters = tts_result["parameters"]
                    
                    st.subheader("🎤 Generated Voice Characteristics")
                    st.write(f"**Voice Description:** {tts_result['voice_description']}")
                    
                    # Parameters table
                    st.subheader("📊 Technical Parameters")
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.metric("Pitch", f"{parameters['pitch']:.0f} Hz")
                        st.metric("Tempo", f"{parameters['tempo']:.0f} BPM")
                        st.metric("Energy", f"{parameters['energy']:.2f}")
                    
                    with col_b:
                        st.metric("Voice Type", parameters['voice_type'].replace('_', ' ').title())
                        st.metric("Emotional Tone", parameters['emotional_tone'].title())
                        st.metric("Brightness", f"{parameters['brightness']:.0f}")
                    
                    # TTS Instructions
                    st.subheader("🔧 TTS Service Instructions")
                    instructions = st.session_state.tts_integration.create_tts_instructions(parameters)
                    
                    st.write("**For Azure Speech Service:**")
                    st.code(f"""
voice = "{instructions['voice']}"
style = "{instructions['style']}"
pitch = "{instructions['prosody']['pitch']}"
rate = "{instructions['prosody']['rate']}"
volume = "{instructions['prosody']['volume']}"
                    """, language="python")
                    
                    # Visualization
                    st.subheader("📈 Voice Characteristics Visualization")
                    
                    # Create radar chart
                    categories = ['Pitch', 'Tempo', 'Energy', 'Brightness', 'Clarity']
                    values = [
                        min(parameters['pitch'] / 200, 1.0),  # Normalize pitch
                        min(parameters['tempo'] / 150, 1.0),  # Normalize tempo
                        parameters['energy'],
                        min(parameters['brightness'] / 3000, 1.0),  # Normalize brightness
                        min(parameters.get('clarity', 0.8), 1.0)  # Use clarity from profile
                    ]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name='Voice Profile'
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )),
                        showlegend=True,
                        title="Voice Characteristics Radar Chart"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.error(f"❌ TTS generation failed: {tts_result['error']}")
    else:
        st.info("👆 Please upload a voice sample first to enable TTS generation")

# Footer
st.markdown("---")
st.markdown("### 🎯 How it works:")
st.markdown("""
1. **Upload a voice sample** - The system analyzes pitch, tempo, energy, and spectral characteristics
2. **Create voice profile** - A unique voice profile is generated based on the analysis
3. **Generate speech parameters** - For any text, the system generates matching voice characteristics
4. **Use with TTS services** - The parameters can be used with Azure Speech, Google TTS, or other services
""")

st.markdown("### 🔧 Supported TTS Services:")
st.markdown("""
- **Azure Speech Service** - Full voice matching with SSML
- **Google Cloud TTS** - Pitch and speed adjustment
- **Amazon Polly** - Voice selection and prosody control
- **ElevenLabs** - Advanced voice cloning capabilities
""")
