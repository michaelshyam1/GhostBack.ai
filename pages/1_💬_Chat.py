import streamlit as st
import re
import openai
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.graph_objects as go
from collections import Counter
import os
from dotenv import load_dotenv
from typing import Dict, List, Any
from safety_analyzer import EmotionalSafetyAnalyzer
from tts_integration import TTSIntegration

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Page configuration
st.set_page_config(
    page_title="Chat - GhostBack.ai",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .top-bar {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        border: 1px solid #667eea30;
    }
</style>
""", unsafe_allow_html=True)

class ChatAnalyzer:
    """Analyzes chat history to extract conversational patterns and style."""
    
    def __init__(self):
        self.patterns = {}
    
    def parse_whatsapp_chat(self, text: str) -> List[Dict[str, str]]:
        """Parse WhatsApp chat export into messages."""
        messages = []
        lines = text.split('\n')
        
        patterns = [
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]\s*([^:]+):\s*(.*)',
            r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\s*-\s*([^:]+):\s*(.*)',
            r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*([^:]+):\s*(.*)',
        ]
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            skip_phrases = [
                'media omitted', 'deleted this message', 'joined using', 'left',
                'changed the subject', 'missed voice call', 'missed video call',
                'encryption', 'security code changed', 'you created group'
            ]
            
            if any(phrase in line.lower() for phrase in skip_phrases):
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    messages.append({
                        'text': groups[3].strip(),
                        'sender': groups[2].strip(),
                        'timestamp': f"{groups[0]} {groups[1]}"
                    })
                    break
        
        return messages
    
    def identify_participants(self, messages: List[Dict[str, str]]) -> tuple:
        """Identify the two main participants."""
        if not messages:
            return None, None
        
        senders = [msg['sender'] for msg in messages]
        sender_counts = Counter(senders)
        
        if len(sender_counts) >= 2:
            top_two = sender_counts.most_common(2)
            return top_two[0][0], top_two[1][0]
        elif len(sender_counts) == 1:
            return list(sender_counts.keys())[0], "Unknown"
        return None, None
    
    def analyze_chat(self, messages: List[Dict[str, str]], ghost_name: str) -> Dict[str, Any]:
        """Analyze the ghost's texting patterns."""
        ghost_messages = [msg for msg in messages if msg['sender'] == ghost_name]
        
        if not ghost_messages:
            return {"error": "No messages found for this person"}
        
        texts = [msg['text'] for msg in ghost_messages]
        all_text = ' '.join(texts)
        
        avg_length = sum(len(t.split()) for t in texts) / len(texts)
        char_length = sum(len(t) for t in texts) / len(texts)
        
        words = re.findall(r'\b\w{3,}\b', all_text.lower())
        common_words = [word for word, count in Counter(words).most_common(10)]
        
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        emojis = emoji_pattern.findall(all_text)
        top_emojis = [emoji for emoji, count in Counter(emojis).most_common(5)]
        
        quirks = []
        text_lower = all_text.lower()
        if text_lower.count('haha') > 2:
            quirks.append("says 'haha' often")
        if text_lower.count('lol') > 2:
            quirks.append("uses 'lol' frequently")
        if text_lower.count('...') > 1:
            quirks.append("uses ellipses")
        if sum(1 for c in all_text if c.isupper()) / max(len(all_text), 1) > 0.15:
            quirks.append("uses caps for emphasis")
        if text_lower.count('omg') > 1:
            quirks.append("says 'omg'")
        
        analyzer = SentimentIntensityAnalyzer()
        sentiments = []
        for text in texts:
            score = analyzer.polarity_scores(text)
            sentiments.append(score['compound'])
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        if avg_sentiment > 0.2:
            tone = "warm and positive"
        elif avg_sentiment < -0.2:
            tone = "distant or cold"
        else:
            tone = "neutral"
        
        starters = []
        for msg in ghost_messages:
            words = msg['text'].split()
            if words:
                first_word = words[0].lower()
                if len(first_word) > 2:
                    starters.append(first_word)
        common_starters = [word for word, count in Counter(starters).most_common(5)]
        
        return {
            "total_messages": len(ghost_messages),
            "avg_words": round(avg_length, 1),
            "avg_chars": round(char_length, 1),
            "common_words": common_words,
            "top_emojis": top_emojis,
            "quirks": quirks,
            "sentiment_scores": sentiments,
            "avg_sentiment": round(avg_sentiment, 3),
            "tone": tone,
            "common_starters": common_starters,
            "sample_messages": texts[:15]  # MORE examples for better learning
        }

class AIPersona:
    """Generates AI persona based on chat analysis."""
    
    def __init__(self):
        pass
    
    def create_system_prompt(self, analysis: Dict[str, Any], ghost_name: str) -> str:
        """Create the system prompt for the AI persona."""
        
        # Get more examples
        examples = analysis['sample_messages'][:10]
        quirks_text = ", ".join(analysis['quirks']) if analysis['quirks'] else "none"
        emojis_text = " ".join(analysis['top_emojis'][:5]) if analysis['top_emojis'] else "none"
        
        prompt = f"""YOU ARE {ghost_name.upper()}. Text EXACTLY like them.

REAL MESSAGES FROM {ghost_name.upper()}:
{chr(10).join([f'{i+1}. "{msg}"' for i, msg in enumerate(examples)])}

THEIR STYLE:
• Length: ~{analysis['avg_words']} words per message
• Tone: {analysis['tone']}
• Quirks: {quirks_text}
• Emojis: {emojis_text}
• Common words: {', '.join(analysis['common_words'][:10])}

RULES:
1. RESPOND DIRECTLY to what the user just said - don't make up previous context
2. Match their texting style: casual, short, their words
3. Use their quirks naturally (lol, haha, etc)
4. Keep it SHORT - they text in ~{analysis['avg_words']} words
5. Don't use formal language or sound like an AI
6. Reply naturally to the ACTUAL message you receive

BAD: "but we can go next week? 😂" (random "but" - what are you responding to?)
GOOD: "next week works! 😂"

You are {ghost_name}. Text like them. Respond to what the user ACTUALLY says."""
        
        return prompt
    
    def generate_response(self, messages: List[Dict], analysis: Dict, ghost_name: str) -> str:
        """Generate AI response based on conversation history."""
        
        if not openai.api_key:
            return "⚠️ OpenAI API key not configured."
        
        try:
            system_prompt = self.create_system_prompt(analysis, ghost_name)
            conversation = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history ONLY (no extra priming that could confuse context)
            for msg in messages[-8:]:  # Last 8 messages for context
                conversation.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            # Calculate token limit based on their style
            target_tokens = int(analysis['avg_words'] * 5)
            max_response_tokens = max(40, min(target_tokens, 150))
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                max_tokens=max_response_tokens,
                temperature=0.85  # Balanced - natural but not too creative
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
def _generate_local_tts_fallback(response: str):
    """Generate local TTS as fallback."""
    with st.spinner("Generating voice..."):
        tts_result = st.session_state.tts_integration.generate_speech_for_message(
            response, is_ai_response=True
        )

        if tts_result["success"]:
            # Display voice characteristics
            st.caption(f"🎤 Voice: {tts_result['voice_description']}")

            # Display TTS parameters for external TTS services
            with st.expander("🔧 TTS Parameters"):
                parameters = tts_result["parameters"]
                st.json({
                    "voice_type": parameters["voice_type"],
                    "pitch": f"{parameters['pitch']:.0f} Hz",
                    "tempo": f"{parameters['tempo']:.0f} BPM",
                    "energy": f"{parameters['energy']:.2f}",
                    "emotional_tone": parameters["emotional_tone"]
                })

                # Generate TTS instructions for external services
                instructions = st.session_state.tts_integration.create_tts_instructions(parameters)
                st.write("**For Azure Speech Service:**")
                st.code(f"""
voice = "{instructions['voice']}"
style = "{instructions['style']}"
pitch = "{instructions['prosody']['pitch']}"
rate = "{instructions['prosody']['rate']}"
volume = "{instructions['prosody']['volume']}"
                """, language="python")
        else:
            st.error(f"TTS generation failed: {tts_result['error']}")

def main():
    """Main application."""
    
    # Header
    st.markdown('<h1 class="main-header">👻 GhostBack.ai</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Find closure through AI-simulated conversations</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None
    if 'ghost_name' not in st.session_state:
        st.session_state.ghost_name = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ChatAnalyzer()
    if 'persona' not in st.session_state:
        st.session_state.persona = AIPersona()
    if 'show_insights' not in st.session_state:
        st.session_state.show_insights = False
    if 'show_closure' not in st.session_state:
        st.session_state.show_closure = False
    
    # Sidebar - Profile info and settings
    with st.sidebar:
        st.title("👻 GhostBack.ai")
        
        # Safety monitoring status
        st.markdown("---")
        st.subheader("🛡️ Safety Monitor")
        st.success("✅ **Active** - Monitoring for emotional safety")
        st.caption("The safety consultant watches over your conversation and provides support when needed.")
        
        # TTS Voice Analysis
        st.markdown("---")
        st.subheader("🎤 Voice Analysis")
        
        # Initialize TTS integration with ElevenLabs
        if 'tts_integration' not in st.session_state:
            # Get ElevenLabs API key from environment
            elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
            if not elevenlabs_key:
                # Use the provided API key
                elevenlabs_key = "sk_56f052abde4435779cd252bf82654fb333801488dacf9f75"
            
            st.session_state.tts_integration = TTSIntegration(elevenlabs_api_key=elevenlabs_key)
        
        # Voice sample upload
        uploaded_voice = st.file_uploader(
            "Upload voice sample (WAV/MP3/M4A)",
            type=['wav', 'mp3', 'm4a'],
            help="Upload a voice sample to analyze and match the person's speaking style. Note: M4A files require FFmpeg to be installed."
        )
        
        # Show M4A requirements info
        with st.expander("ℹ️ M4A File Requirements"):
            st.write("**M4A files require FFmpeg to be installed on your system.**")
            st.write("If you encounter errors with M4A files, please:")
            st.write("1. **Install FFmpeg** (recommended):")
            st.write("   - Windows: `choco install ffmpeg` (if you have Chocolatey)")
            st.write("   - Or download from: https://ffmpeg.org/download.html")
            st.write("2. **Convert to WAV/MP3** instead (easier option)")
            st.write("3. **Use online converters** to convert M4A to WAV")
        
        if uploaded_voice is not None:
            with st.spinner("Analyzing voice sample..."):
                result = st.session_state.tts_integration.process_voice_sample(uploaded_voice)
                
            if result["success"]:
                file_format = result.get('file_format', 'unknown').upper()
                st.success(f"✅ Voice profile created! (Format: {file_format})")

                # Display voice characteristics
                profile_summary = st.session_state.tts_integration.get_voice_profile_summary()
                if profile_summary:
                    st.write("**Voice Characteristics:**")
                    st.write(f"• Type: {profile_summary['voice_type']}")
                    st.write(f"• Tone: {profile_summary['emotional_tone']}")
                    st.write(f"• Pitch: {profile_summary['base_pitch']:.0f} Hz")
                    st.write(f"• Tempo: {profile_summary['tempo']:.0f} BPM")
                    st.write(f"• Clarity: {profile_summary['clarity']:.2f}")
                    st.write(f"• Format: {file_format}")
            else:
                st.error(f"❌ Voice analysis failed: {result['error']}")
        
        # TTS Settings
        st.markdown("---")
        st.subheader("🔊 Text-to-Speech")
        
        enable_tts = st.checkbox("Enable TTS for AI responses", value=False, key="enable_tts")
        if enable_tts:
            # Check for ElevenLabs cloned voice
            has_elevenlabs_voice = (st.session_state.tts_integration.elevenlabs and 
                                  st.session_state.tts_integration.elevenlabs.voice_id)
            
            if has_elevenlabs_voice:
                st.success("🎭 Cloned voice enabled")
                st.caption(f"AI responses will be spoken in {st.session_state.ghost_name}'s cloned voice")
                
                # Show voice info
                voice_info = st.session_state.tts_integration.get_elevenlabs_voice_info()
                if voice_info and 'error' not in voice_info:
                    st.info(f"**Voice:** {voice_info['name']}")
            elif st.session_state.get('cloned_voice_id'):
                st.info("🎭 Cloned voice available from Voice Cloning page")
                if st.button("🔄 Transfer Cloned Voice", key="transfer_voice"):
                    if st.session_state.tts_integration.elevenlabs:
                        st.session_state.tts_integration.elevenlabs.voice_id = st.session_state.cloned_voice_id
                        st.session_state.tts_integration.elevenlabs.voice_name = st.session_state.get('cloned_voice_name', 'Cloned Voice')
                        st.success("✅ Voice transferred! Enable TTS to use it.")
                        st.rerun()
            elif st.session_state.tts_integration.voice_profile:
                st.success("✅ Voice matching enabled")
                st.caption("AI responses will be generated with matching voice characteristics")
            else:
                st.warning("⚠️ Upload a voice sample to enable voice matching")
                st.info("💡 Go to the Voice Cloning page to create a cloned voice!")
        
        if st.session_state.analysis:
            st.markdown("---")
            st.subheader(f"📊 {st.session_state.ghost_name}'s Profile")
            
            analysis = st.session_state.analysis
            
            col1, col2 = st.columns(2)
            col1.metric("Messages", analysis['total_messages'])
            col2.metric("Avg Length", f"{analysis['avg_words']} words")
            
            st.metric("Tone", analysis['tone'].title())
            st.metric("Sentiment", f"{analysis['avg_sentiment']:.2f}")
            
            if analysis['quirks']:
                st.markdown("**Quirks:**")
                for quirk in analysis['quirks'][:3]:
                    st.caption(f"• {quirk}")
            
            if analysis['top_emojis']:
                st.markdown("**Favorite emojis:**")
                st.write(" ".join(analysis['top_emojis'][:5]))
            
            st.markdown("---")
            
            if st.button("🗑️ Clear & Start Over", use_container_width=True):
                st.session_state.clear()
                st.switch_page("app.py")
        else:
            st.info("Upload a chat to get started")
    
    # TOP BAR - Action buttons (when analysis is ready)
    if st.session_state.analysis:
        st.markdown('<div class="top-bar">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("📊 View Insights", use_container_width=True):
                st.session_state.show_insights = not st.session_state.show_insights
                st.session_state.show_closure = False
                st.rerun()
        
        with col2:
            if st.button("💭 Closure Letter", use_container_width=True):
                st.session_state.show_closure = not st.session_state.show_closure
                st.session_state.show_insights = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show insights panel if toggled
        if st.session_state.show_insights:
            with st.expander("📈 Conversation Insights", expanded=True):
                analysis = st.session_state.analysis
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Messages", analysis['total_messages'])
                col2.metric("Average Words", analysis['avg_words'])
                col3.metric("Emotional Tone", analysis['tone'].title())
                
                if analysis['sentiment_scores']:
                    st.markdown("**Original Chat Sentiment**")
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        y=analysis['sentiment_scores'],
                        mode='lines+markers',
                        line=dict(color='#667eea', width=2),
                        marker=dict(size=4, color='#764ba2'),
                        fill='tozeroy',
                        fillcolor='rgba(102, 126, 234, 0.1)'
                    ))
                    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
                    fig.update_layout(
                        height=250,
                        margin=dict(l=10, r=10, t=10, b=10),
                        yaxis_title="Sentiment",
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        yaxis=dict(range=[-1, 1])
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                if len(st.session_state.chat_history) > 0:
                    st.markdown("**Current Conversation Sentiment**")
                    
                    analyzer = SentimentIntensityAnalyzer()
                    user_sentiments = []
                    ai_sentiments = []
                    
                    for msg in st.session_state.chat_history:
                        score = analyzer.polarity_scores(msg['content'])['compound']
                        if msg['role'] == 'user':
                            user_sentiments.append(score)
                        else:
                            ai_sentiments.append(score)
                    
                    fig2 = go.Figure()
                    if user_sentiments:
                        fig2.add_trace(go.Scatter(
                            y=user_sentiments,
                            mode='lines+markers',
                            line=dict(color='#4CAF50', width=2),
                            name='You'
                        ))
                    if ai_sentiments:
                        fig2.add_trace(go.Scatter(
                            y=ai_sentiments,
                            mode='lines+markers',
                            line=dict(color='#FF6B6B', width=2),
                            name=st.session_state.ghost_name
                        ))
                    
                    fig2.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
                    fig2.update_layout(
                        height=250,
                        margin=dict(l=10, r=10, t=10, b=10),
                        yaxis_title="Sentiment",
                        showlegend=True,
                        yaxis=dict(range=[-1, 1])
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    if user_sentiments:
                        avg_new = sum(user_sentiments) / len(user_sentiments)
                        avg_old = analysis['avg_sentiment']
                        change = avg_new - avg_old
                        st.metric(
                            "Your Emotional Shift", 
                            f"{avg_new:.2f}",
                            f"{change:+.2f} from original"
                        )
        
        # Show closure letter if toggled
        if st.session_state.show_closure:
            with st.expander("💭 Your Closure Letter", expanded=True):
                if 'closure_letter' not in st.session_state:
                    with st.spinner("Writing your closure letter..."):
                        try:
                            analysis = st.session_state.analysis
                            prompt = f"""Based on this chat analysis, write 2-3 compassionate paragraphs to help someone find closure.

Person: {st.session_state.ghost_name}
Total messages: {analysis['total_messages']}
Their average message length: {analysis['avg_words']} words
Emotional tone: {analysis['tone']}
Sentiment score: {analysis['avg_sentiment']}

Write gentle, honest observations about their communication style. Be compassionate but truthful. Help them understand and find peace."""

                            response = openai.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=400,
                                temperature=0.7
                            )
                            
                            st.session_state.closure_letter = response.choices[0].message.content
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                if 'closure_letter' in st.session_state:
                    st.write(st.session_state.closure_letter)
    
    # MAIN CONTENT AREA
    if not st.session_state.analysis:
        # UPLOAD PHASE - Main page
        st.markdown("## 📱 Upload Your Chat History")
        
        st.info("""
        **How to export WhatsApp chat:**
        1. Open the chat in WhatsApp
        2. Tap the contact/group name → Export Chat → Without Media
        3. Copy the text and paste below
        """)
        
        chat_text = st.text_area(
            "Paste your chat export here",
            height=300,
            placeholder="[1/15/24, 10:30 PM] John: hey\n[1/15/24, 10:32 PM] You: hi"
        )
        
        if st.button("🔍 Analyze Chat", type="primary"):
            if not chat_text.strip():
                st.error("Please paste some chat text first!")
            else:
                with st.spinner("Parsing messages..."):
                    messages = st.session_state.analyzer.parse_whatsapp_chat(chat_text)
                    
                    if len(messages) < 5:
                        st.error(f"Only found {len(messages)} messages. Need at least 5.")
                    else:
                        st.session_state.parsed_messages = messages
                        person1, person2 = st.session_state.analyzer.identify_participants(messages)
                        
                        if person1 and person2:
                            st.session_state.participants = (person1, person2)
                            st.success(f"Found {len(messages)} messages!")
                            st.rerun()
        
        # PARTICIPANT SELECTION - Main page
        if 'participants' in st.session_state:
            st.markdown("---")
            st.markdown("## 💬 Who do you want to talk to?")
            
            person1, person2 = st.session_state.participants
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"💬 {person1}", use_container_width=True, type="primary"):
                    with st.spinner("Analyzing their texting style..."):
                        analysis = st.session_state.analyzer.analyze_chat(
                            st.session_state.parsed_messages,
                            person1
                        )
                        
                        if "error" not in analysis:
                            st.session_state.analysis = analysis
                            st.session_state.ghost_name = person1
                            st.session_state.chat_history = []
                            del st.session_state.parsed_messages
                            del st.session_state.participants
                            st.success(f"✅ Ready to chat with {person1}!")
                            st.rerun()
            
            with col2:
                if st.button(f"💬 {person2}", use_container_width=True, type="primary"):
                    with st.spinner("Analyzing their texting style..."):
                        analysis = st.session_state.analyzer.analyze_chat(
                            st.session_state.parsed_messages,
                            person2
                        )
                        
                        if "error" not in analysis:
                            st.session_state.analysis = analysis
                            st.session_state.ghost_name = person2
                            st.session_state.chat_history = []
                            del st.session_state.parsed_messages
                            del st.session_state.participants
                            st.success(f"✅ Ready to chat with {person2}!")
                            st.rerun()
    
    else:
        # CHAT INTERFACE
        st.markdown(f"### 💬 Chat with {st.session_state.ghost_name}")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show audio controls if message has audio data
                if message.get("audio_data") and message["role"] == "assistant":
                    if message.get("voice_type") == "cloned":
                        st.audio(message["audio_data"], format="audio/mp3")
                        st.caption(f"🎭 {st.session_state.ghost_name}'s cloned voice")
                    else:
                        st.audio(message["audio_data"], format="audio/wav")
                        st.caption("🎤 Generated voice")
        
        # Chat input
        if prompt := st.chat_input(f"Message {st.session_state.ghost_name}..."):
            # Initialize safety analyzer if not exists
            if 'safety_analyzer' not in st.session_state:
                st.session_state.safety_analyzer = EmotionalSafetyAnalyzer()
            
            # Safety analysis of user message
            safety_analysis = st.session_state.safety_analyzer.analyze_message_safety(prompt)
            
            # Add user message
            st.session_state.chat_history.append({
                "role": "user",
                "content": prompt
            })
            
            # Show user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Show safety warning if needed
            if safety_analysis['warning_level'] != 'none':
                warning_level = safety_analysis['warning_level']
                warning_colors = {
                    'low': '🟡',
                    'medium': '🟠', 
                    'high': '🔴',
                    'crisis': '🚨'
                }
                
                with st.chat_message("assistant"):
                    st.warning(f"{warning_colors.get(warning_level, '⚠️')} **Safety Alert - {warning_level.upper()}**")
                    
                    for warning in safety_analysis['warnings']:
                        st.write(f"• {warning['message']}")
                    
                    if warning_level == 'crisis':
                        st.error("**IMMEDIATE SUPPORT NEEDED**")
                        st.write("Please call a crisis helpline immediately:")
                        st.write("• **988** (US National Suicide Prevention Lifeline)")
                        st.write("• **Text HOME to 741741** (Crisis Text Line)")
                        st.write("• **Your local emergency number**")
                        st.stop()  # Stop the conversation for crisis
                    elif warning_level == 'high':
                        st.error("**EMOTIONAL OVERLOAD DETECTED**")
                        st.write("Please take a break and care for yourself.")
                        st.write("Consider talking to someone you trust about how you're feeling.")
                        st.stop()  # Pause conversation for high risk
            
            # Generate AI response (only if not stopped by safety)
            with st.chat_message("assistant"):
                with st.spinner(f"{st.session_state.ghost_name} is typing..."):
                    response = st.session_state.persona.generate_response(
                        st.session_state.chat_history,
                        st.session_state.analysis,
                        st.session_state.ghost_name
                    )
                    st.write(response)
            
            # Generate TTS if enabled
            if st.session_state.get('enable_tts', False):
                # Check if we have ElevenLabs cloned voice available
                has_elevenlabs_voice = (st.session_state.tts_integration.elevenlabs and 
                                      st.session_state.tts_integration.elevenlabs.voice_id)
                
                # Check if we have a cloned voice from the voice cloning page
                if st.session_state.get('cloned_voice_id') and not has_elevenlabs_voice:
                    # Transfer the voice ID to the TTS integration
                    if st.session_state.tts_integration.elevenlabs:
                        st.session_state.tts_integration.elevenlabs.voice_id = st.session_state.cloned_voice_id
                        st.session_state.tts_integration.elevenlabs.voice_name = st.session_state.get('cloned_voice_name', 'Cloned Voice')
                        has_elevenlabs_voice = True
                        st.success("✅ Cloned voice transferred from Voice Cloning page!")
                
                if has_elevenlabs_voice:
                    # Use ElevenLabs cloned voice
                    with st.spinner("🎭 Generating speech with cloned voice..."):
                        tts_result = st.session_state.tts_integration.generate_speech_elevenlabs(response)
                        
                        if tts_result["success"]:
                            # Play the audio automatically
                            st.audio(tts_result["audio_data"], format="audio/mp3", autoplay=True)
                            st.caption(f"🎤 Speaking as {st.session_state.ghost_name} (cloned voice)")
                            
                            # Store audio in chat history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": response,
                                "audio_data": tts_result["audio_data"],
                                "voice_type": "cloned"
                            })
                        else:
                            st.error(f"❌ Cloned voice generation failed: {tts_result['error']}")
                            # Fallback to local TTS
                            _generate_local_tts_fallback(response)
                            # Add to history without audio
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": response
                            })
                else:
                    # Use local TTS as fallback
                    _generate_local_tts_fallback(response)
                    # Add to history without audio
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
            else:
                # No TTS - just add to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
            
            st.rerun()
        
        # Audio generation buttons - ALWAYS VISIBLE when TTS is enabled
        if st.session_state.get('enable_tts', False) and st.session_state.chat_history:
            # Get the last assistant message
            last_assistant_message = None
            for message in reversed(st.session_state.chat_history):
                if message["role"] == "assistant":
                    last_assistant_message = message
                    break
            
            if last_assistant_message:
                st.subheader("🔊 Generate Audio for Last Response")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("🔊 Generate Audio (Local)", key="generate_local_audio"):
                        st.write("🔄 Generating local audio...")
                        try:
                            # Try simple method first
                            audio_result = st.session_state.tts_integration.generate_audio_simple(last_assistant_message["content"])
                            
                            if not audio_result["success"]:
                                # Fallback to original method
                                st.write("⚠️ Trying alternative method...")
                                audio_result = st.session_state.tts_integration.generate_audio_file(last_assistant_message["content"])
                            
                            if audio_result["success"]:
                                st.audio(audio_result["audio_data"], format="audio/wav")
                                st.success("✅ Audio generated successfully!")
                                st.write(f"📊 Audio size: {len(audio_result['audio_data'])} bytes")
                            else:
                                st.error(f"❌ Audio generation failed: {audio_result['error']}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                with col2:
                    if st.button("🌐 Generate Audio (Google)", key="generate_google_audio"):
                        st.write("🔄 Generating Google TTS audio...")
                        try:
                            audio_result = st.session_state.tts_integration.generate_audio_gtts(last_assistant_message["content"])
                            
                            if audio_result["success"]:
                                st.audio(audio_result["audio_data"], format="audio/mp3")
                                st.success("✅ Google TTS audio generated!")
                                st.write(f"📊 Audio size: {len(audio_result['audio_data'])} bytes")
                            else:
                                st.error(f"❌ Google TTS failed: {audio_result['error']}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            

if __name__ == "__main__":
    main()