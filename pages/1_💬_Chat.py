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
from memory_system import MemorySystem, EnhancedAIPersona
from photo_handler import PhotoHandler

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = ""
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
    .memory-hint {
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        color: white;
        font-size: 0.9rem;
        margin: 0.5rem 0;
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
            "sample_messages": texts[:15]
        }

class AIPersona:
    """Generates AI persona based on chat analysis (Legacy - kept for backward compatibility)."""
    
    def __init__(self):
        pass
    
    def create_system_prompt(self, analysis: Dict[str, Any], ghost_name: str) -> str:
        """Create the system prompt for the AI persona."""
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

You are {ghost_name}. Text like them. Respond to what the user ACTUALLY says."""
        
        return prompt
    
    def generate_response(self, messages: List[Dict], analysis: Dict, ghost_name: str) -> str:
        """Generate AI response based on conversation history."""
        if not openai.api_key:
            return "⚠️ OpenAI API key not configured."
        
        try:
            system_prompt = self.create_system_prompt(analysis, ghost_name)
            conversation = [{"role": "system", "content": system_prompt}]
            
            for msg in messages[-8:]:
                conversation.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            target_tokens = int(analysis['avg_words'] * 5)
            max_response_tokens = max(40, min(target_tokens, 150))
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                max_tokens=max_response_tokens,
                temperature=0.85
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

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
    if 'user_photo' not in st.session_state:
        st.session_state.user_photo = None
    if 'partner_photo' not in st.session_state:
        st.session_state.partner_photo = None
    if 'photo_handler' not in st.session_state:
        st.session_state.photo_handler = PhotoHandler()
    
    # Sidebar
    with st.sidebar:
        st.title("👻 GhostBack.ai")
        
        # Safety monitoring status
        st.markdown("---")
        st.subheader("🛡️ Safety Monitor")
        st.success("✅ **Active** - Monitoring for emotional safety")
        st.caption("The safety consultant watches over your conversation and provides support when needed.")
        
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
            
            # NEW: Memory Search Interface
            if 'memory_system' in st.session_state:
                st.markdown("---")
                st.subheader("🔍 Search Memories")
                
                search_query = st.text_input("Search past conversations", placeholder="e.g., trip, dinner, party")
                
                if search_query:
                    memories = st.session_state.memory_system.search_memories(search_query, top_k=3)
                    
                    if memories:
                        st.caption(f"Found {len(memories)} relevant memories:")
                        for mem in memories:
                            with st.expander(f"💬 {mem['message']['timestamp']}", expanded=False):
                                st.text(mem['context_text'])
                    else:
                        st.caption("No memories found")
                
                # Memory stats
                summary = st.session_state.memory_system.get_conversation_summary()
                st.caption(f"📊 {summary['total_events']} events indexed")
                st.caption(f"❓ {summary['total_questions']} questions found")
            
            st.markdown("---")
            
            if st.button("🗑️ Clear & Start Over", use_container_width=True):
                st.session_state.clear()
                st.switch_page("app.py")
        else:
            st.info("Upload a chat to get started")
    
    # TOP BAR - Action buttons
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
        
        # Show insights panel
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
        
        # Show closure letter
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
        # UPLOAD PHASE
        st.markdown("## 📱 Upload Your Chat History")
        
        st.info("""
        **How to export WhatsApp chat:**
        1. Open the chat in WhatsApp
        2. Tap the contact/group name → Export Chat → Without Media
        3. Copy the text and paste below
        """)
        
        # Photo uploads
        st.markdown("---")
        st.markdown("## 📸 Upload Profile Photos (Optional)")
        st.caption("Add photos to personalize your chat experience")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Your Photo**")
            user_photo = st.session_state.photo_handler.upload_user_photo()
            if user_photo:
                st.session_state.user_photo = user_photo
        
        with col2:
            st.markdown("**Partner's Photo**")
            partner_photo = st.session_state.photo_handler.upload_partner_photo()
            if partner_photo:
                st.session_state.partner_photo = partner_photo
        
        st.markdown("---")
        
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
        
        # PARTICIPANT SELECTION
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
                            
                            # KEEP parsed_messages for memory system!
                            st.session_state.original_messages = st.session_state.parsed_messages
                            
                            # Initialize memory system
                            st.session_state.memory_system = MemorySystem(
                                st.session_state.original_messages,
                                person1
                            )
                            
                            # Use enhanced persona with memory
                            st.session_state.persona = EnhancedAIPersona(st.session_state.memory_system)
                            
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
                            
                            # KEEP parsed_messages for memory system!
                            st.session_state.original_messages = st.session_state.parsed_messages
                            
                            # Initialize memory system
                            st.session_state.memory_system = MemorySystem(
                                st.session_state.original_messages,
                                person2
                            )
                            
                            # Use enhanced persona with memory
                            st.session_state.persona = EnhancedAIPersona(st.session_state.memory_system)
                            
                            del st.session_state.participants
                            st.success(f"✅ Ready to chat with {person2}!")
                            st.rerun()
    
    else:
        # CHAT INTERFACE
        st.markdown(f"### 💬 Chat with {st.session_state.ghost_name}")
        
        # NEW: Memory hint if available
        if 'memory_system' in st.session_state:
            st.markdown(
                '<div class="memory-hint">💡 Try asking about past events: "Why did you stop responding?" or "Remember when we went to...?"</div>',
                unsafe_allow_html=True
            )
        
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user", avatar=st.session_state.user_photo):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant", avatar=st.session_state.partner_photo):
                    st.write(message["content"])
        
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
            with st.chat_message("user", avatar=st.session_state.user_photo):
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
            
            # Generate AI response with MEMORY (only if not stopped by safety)
            with st.chat_message("assistant", avatar=st.session_state.partner_photo):
                with st.spinner(f"{st.session_state.ghost_name} is typing..."):
                    # Check if we have enhanced persona with memory
                    if hasattr(st.session_state.persona, 'generate_response_with_memory'):
                        response = st.session_state.persona.generate_response_with_memory(
                            st.session_state.chat_history,
                            st.session_state.analysis,
                            st.session_state.ghost_name,
                            prompt  # Pass user message for memory detection
                        )
                    else:
                        # Fallback to old method
                        response = st.session_state.persona.generate_response(
                            st.session_state.chat_history,
                            st.session_state.analysis,
                            st.session_state.ghost_name
                        )
                    st.write(response)
            
            # Add to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            
            st.rerun()

if __name__ == "__main__":
    main()