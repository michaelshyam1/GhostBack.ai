import streamlit as st
import re
import openai
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.graph_objects as go
from collections import Counter
import os
from dotenv import load_dotenv
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("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")

# Page configuration
st.set_page_config(
    page_title="GhostBack.ai",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    .stChatMessage {
        background-color: transparent;
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
        
        # Multiple WhatsApp format patterns
        patterns = [
            # iOS: [1/15/24, 10:30:25 PM] John: message
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]\s*([^:]+):\s*(.*)',
            # Android: 1/15/24, 10:30 PM - John: message
            r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\s*-\s*([^:]+):\s*(.*)',
            # Alternative: 15/1/24, 22:30 - John: message
            r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*([^:]+):\s*(.*)',
        ]
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip system messages
            skip_phrases = [
                'media omitted', 'deleted this message', 'joined using', 'left',
                'changed the subject', 'missed voice call', 'missed video call',
                'encryption', 'security code changed', 'you created group'
            ]
            
            if any(phrase in line.lower() for phrase in skip_phrases):
                continue
            
            # Try each pattern
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
        
        # Text analysis
        texts = [msg['text'] for msg in ghost_messages]
        all_text = ' '.join(texts)
        
        # Message length
        avg_length = sum(len(t.split()) for t in texts) / len(texts)
        char_length = sum(len(t) for t in texts) / len(texts)
        
        # Common words (excluding very short ones)
        words = re.findall(r'\b\w{3,}\b', all_text.lower())
        common_words = [word for word, count in Counter(words).most_common(10)]
        
        # Emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        emojis = emoji_pattern.findall(all_text)
        top_emojis = [emoji for emoji, count in Counter(emojis).most_common(5)]
        
        # Quirks detection
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
        
        # Sentiment analysis with VADER
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
        
        # Common sentence starters
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
            "sample_messages": texts[:5]
        }

class AIPersona:
    """Generates AI persona based on chat analysis."""
    
    def __init__(self):
        pass
    
    def create_system_prompt(self, analysis: Dict[str, Any], ghost_name: str) -> str:
        """Create the system prompt for the AI persona."""
        
        quirks_text = ", ".join(analysis['quirks']) if analysis['quirks'] else "no specific quirks detected"
        emojis_text = " ".join(analysis['top_emojis'][:3]) if analysis['top_emojis'] else "rarely uses emojis"
        
        prompt = f"""You are helping someone find closure by simulating text conversations with someone from their past named {ghost_name}.

THEIR ORIGINAL TEXTING STYLE:
- Average message length: {analysis['avg_words']} words
- Emotional tone: {analysis['tone']}
- Common words: {', '.join(analysis['common_words'][:5])}
- Quirks: {quirks_text}
- Emojis: {emojis_text}
- Often starts with: {', '.join(analysis['common_starters'][:3])}

EXAMPLES OF THEIR MESSAGES:
{chr(10).join([f'- "{msg}"' for msg in analysis['sample_messages'][:3]])}

CRITICAL RULES FOR THIS CLOSURE CONVERSATION:
1. BASE STYLE: Use their casual texting style as a foundation - quirks, tone, informal language
2. EMOTIONAL INTELLIGENCE: When the user sends a long, vulnerable, or emotional message, RESPOND WITH DEPTH. Don't just send a one-liner back. This is about closure, not just mimicking brevity.
3. MATCH THEIR ENERGY: 
   - If they send 2 words → respond with similar brevity
   - If they send a heartfelt paragraph → respond with 3-5 thoughtful sentences
   - If they ask deep questions → give honest, meaningful answers
4. BE AUTHENTIC: Text like {ghost_name} would IF they were actually being emotionally honest and available (which they might not have been originally)
5. DON'T BE A THERAPIST: Sound like a real person having a real conversation, not a counselor
6. NO AI DISCLAIMERS: Don't mention being an AI unless directly asked
7. VULNERABILITY: If the user is being vulnerable, honor that with a real response, not deflection
8. CLOSURE FOCUS: This conversation is meant to help them process and heal - be emotionally present

Remember: You're simulating how {ghost_name} WOULD communicate if they were being honest and emotionally available. Match their style but with emotional depth appropriate to what the user is sharing."""
        
        return prompt
    
    def generate_response(self, messages: List[Dict], analysis: Dict, ghost_name: str) -> str:
        """Generate AI response based on conversation history."""
        
        if not os.getenv("OPENAI_API_KEY"):
            return "⚠️ Please add your OpenAI API key in the sidebar to enable chat."
        
        try:
            system_prompt = self.create_system_prompt(analysis, ghost_name)
            
            # Build conversation history for context
            conversation = [{"role": "system", "content": system_prompt}]
            
            # Add last 10 messages for context
            for msg in messages[-10:]:
                conversation.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                max_tokens=150,
                temperature=0.9
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
    
    # Sidebar
    with st.sidebar:
        st.header("📱 Upload Chat")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Get your key from platform.openai.com"
        )
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            openai.api_key = api_key
        
        st.markdown("---")
        
        # File upload
        st.markdown("**How to export WhatsApp chat:**")
        st.caption("Open chat → Menu → More → Export chat → Without media → Copy & paste below")
        
        chat_text = st.text_area(
            "Paste your chat export here",
            height=200,
            placeholder="[1/15/24, 10:30 PM] John: hey\n[1/15/24, 10:32 PM] You: hi"
        )
        
        if st.button("🔍 Analyze Chat", type="primary"):
            if not chat_text.strip():
                st.error("Please paste some chat text first!")
            else:
                with st.spinner("Parsing messages..."):
                    messages = st.session_state.analyzer.parse_whatsapp_chat(chat_text)
                    
                    if len(messages) < 5:
                        st.error(f"Only found {len(messages)} messages. Need at least 5. Check the format!")
                        st.info("Expected format:\n[date, time] Name: message")
                    else:
                        # STORE MESSAGES IN SESSION STATE
                        st.session_state.parsed_messages = messages
                        
                        # Identify participants
                        person1, person2 = st.session_state.analyzer.identify_participants(messages)
                        
                        if not person1 or not person2:
                            st.error("Couldn't identify participants. Check format.")
                        else:
                            st.success(f"Found {len(messages)} messages!")
                            st.session_state.participants = (person1, person2)
        
        # Show participant selection if messages are parsed
        if 'parsed_messages' in st.session_state and 'participants' in st.session_state:
            st.markdown("**Who do you want to talk to?**")
            person1, person2 = st.session_state.participants
            
            ghost_choice = st.radio(
                "Select the person:",
                [person1, person2],
                key="ghost_selector"
            )
            
            if st.button("Continue"):
                with st.spinner("Analyzing texting patterns..."):
                    analysis = st.session_state.analyzer.analyze_chat(
                        st.session_state.parsed_messages,
                        ghost_choice
                    )
                    
                    if "error" in analysis:
                        st.error(analysis["error"])
                    else:
                        st.session_state.analysis = analysis
                        st.session_state.ghost_name = ghost_choice
                        st.session_state.chat_history = []
                        
                        # Clear the temporary data
                        del st.session_state.parsed_messages
                        del st.session_state.participants
                        
                        st.success(f"✅ Ready to chat with {ghost_choice}!")
                        st.rerun()
        
        # Show analysis if ready
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
            
            # Insights in sidebar
            with st.expander("📈 View Insights"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Messages", analysis['total_messages'])
                col2.metric("Average Words", analysis['avg_words'])
                col3.metric("Emotional Tone", analysis['tone'].title())
                
                # Original chat sentiment timeline
                if analysis['sentiment_scores']:
                    st.markdown("**Original Chat Sentiment**")
                    st.caption("Emotional tone from the WhatsApp export")
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        y=analysis['sentiment_scores'],
                        mode='lines+markers',
                        line=dict(color='#667eea', width=2),
                        marker=dict(size=4, color='#764ba2'),
                        fill='tozeroy',
                        fillcolor='rgba(102, 126, 234, 0.1)',
                        name='Original'
                    ))
                    
                    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
                    
                    fig.update_layout(
                        height=200,
                        margin=dict(l=10, r=10, t=10, b=10),
                        yaxis_title="Sentiment",
                        xaxis_title="Message",
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        yaxis=dict(range=[-1, 1])
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # NEW: Current conversation sentiment
                if len(st.session_state.chat_history) > 0:
                    st.markdown("**Current Conversation Sentiment**")
                    st.caption("Emotional tone of this closure conversation")
                    
                    # Analyze sentiment of current chat
                    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
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
                            marker=dict(size=5),
                            name='Your messages'
                        ))
                    
                    if ai_sentiments:
                        fig2.add_trace(go.Scatter(
                            y=ai_sentiments,
                            mode='lines+markers',
                            line=dict(color='#FF6B6B', width=2),
                            marker=dict(size=5),
                            name=f"{st.session_state.ghost_name}'s responses"
                        ))
                    
                    fig2.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
                    
                    fig2.update_layout(
                        height=200,
                        margin=dict(l=10, r=10, t=10, b=10),
                        yaxis_title="Sentiment",
                        xaxis_title="Exchange",
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        plot_bgcolor='rgba(0,0,0,0)',
                        yaxis=dict(range=[-1, 1])
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # Show average change
                    if user_sentiments:
                        avg_new = sum(user_sentiments) / len(user_sentiments)
                        avg_old = analysis['avg_sentiment']
                        change = avg_new - avg_old
                        
                        st.metric(
                            "Your Emotional Shift", 
                            f"{avg_new:.2f}",
                            f"{change:+.2f} from original",
                            delta_color="normal" if change > 0 else "inverse"
                        )
                
                if analysis['common_words']:
                    st.markdown("**Common Words**")
                    st.caption(", ".join(analysis['common_words'][:8]))
            
            # Closure letter in sidebar
            with st.expander("💭 Generate Closure Letter"):
                if st.button("Generate Letter", type="primary"):
                    if not os.getenv("OPENAI_API_KEY"):
                        st.error("Please add your OpenAI API key above.")
                    else:
                        with st.spinner("Writing..."):
                            try:
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
                                
                                st.write(response.choices[0].message.content)
                                
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            st.markdown("---")
            
            if st.button("🗑️ Clear & Start Over"):
                st.session_state.clear()
                st.rerun()
    
    # Main content
    if not st.session_state.analysis:
        # Welcome screen
        st.info("👈 **Get started:** Paste your WhatsApp chat export in the sidebar")
        
        st.markdown("### How it works")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**1️⃣ Upload**")
            st.caption("Paste your WhatsApp chat history")
        
        with col2:
            st.markdown("**2️⃣ Analyze**")
            st.caption("AI learns their texting style")
        
        with col3:
            st.markdown("**3️⃣ Chat**")
            st.caption("Talk to an AI simulation for closure")
        
        st.markdown("---")
        
        st.markdown("### Sample Chat Format")
        st.code("""[1/15/24, 10:30 PM] Alex: hey what's up
[1/15/24, 10:32 PM] Jordan: not much haha
[1/15/24, 10:33 PM] Alex: wanna hang out?
[1/15/24, 10:35 PM] Jordan: maybe later""")
        
        st.warning("⚠️ **Privacy Notice:** All data stays in this session. Nothing is stored or shared.")
        
    else:
        # Chat interface
        st.markdown(f"### 💬 Chat with {st.session_state.ghost_name}")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Type your message..."):
            # Add user message
            st.session_state.chat_history.append({
                "role": "user",
                "content": prompt
            })
            
            # Show user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner(f"{st.session_state.ghost_name} is typing..."):
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