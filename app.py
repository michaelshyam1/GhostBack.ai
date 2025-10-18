import streamlit as st
import re
import openai
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.graph_objects as go
from collections import Counter
import os
from dotenv import load_dotenv
from typing import Dict, List, Any
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure AI Providers
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ollama configuration
OLLAMA_ENDPOINT = "http://localhost:11434"
AVAILABLE_MODELS = [
    "mistral:7b-instruct",
    "llama3.1:8b-instruct", 
    "llama3.1:70b-instruct",
    "codellama:7b-instruct",
    "phi3:3.8b-instruct",
    "gemma2:9b-instruct"
]
DEFAULT_MODEL = "mistral:7b-instruct"

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
    """Generates AI persona based on chat analysis with advanced features."""
    
    def __init__(self):
        self.conversation_memory = []
        self.emotional_state = "neutral"
        self.personality_adaptations = {}
        self.context_history = []
    
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
    
    def update_emotional_state(self, user_message: str, conversation_history: List[Dict]) -> str:
        """Track and update emotional state based on conversation flow."""
        analyzer = SentimentIntensityAnalyzer()
        
        # Analyze current user message
        current_sentiment = analyzer.polarity_scores(user_message)['compound']
        
        # Analyze recent conversation context
        recent_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        recent_sentiments = []
        
        for msg in recent_messages:
            if msg['role'] == 'user':
                score = analyzer.polarity_scores(msg['content'])['compound']
                recent_sentiments.append(score)
        
        # Determine emotional state
        if current_sentiment > 0.3:
            self.emotional_state = "positive"
        elif current_sentiment < -0.3:
            self.emotional_state = "negative"
        elif len(recent_sentiments) > 0 and sum(recent_sentiments) / len(recent_sentiments) < -0.2:
            self.emotional_state = "concerned"
        elif len(recent_sentiments) > 0 and sum(recent_sentiments) / len(recent_sentiments) > 0.2:
            self.emotional_state = "hopeful"
        else:
            self.emotional_state = "neutral"
        
        return self.emotional_state
    
    def extract_memory_items(self, user_message: str, conversation_history: List[Dict]) -> List[str]:
        """Extract key details to remember from the conversation."""
        memory_items = []
        
        # Look for important details in user messages
        important_patterns = [
            r"(?:my|i|me|we|us|our)\s+(?:name|job|work|family|friend|partner|relationship|life|dream|goal|fear|worry|hope|plan)",
            r"(?:remember|recall|think about|miss|regret|wish|want|need|feel)",
            r"(?:important|significant|special|meaningful|difficult|hard|easy|good|bad)",
        ]
        
        for pattern in important_patterns:
            matches = re.findall(pattern, user_message.lower())
            if matches:
                memory_items.extend(matches)
        
        # Store in conversation memory
        if memory_items:
            self.conversation_memory.extend(memory_items[:3])  # Limit to 3 items per message
        
        return memory_items
    
    def adapt_personality(self, conversation_history: List[Dict], ghost_name: str) -> Dict[str, str]:
        """Dynamically adapt personality based on conversation flow."""
        adaptations = {}
        
        # Analyze conversation length and depth
        if len(conversation_history) > 10:
            adaptations['depth'] = "deeper"
            adaptations['approach'] = "more reflective"
        
        # Analyze emotional patterns
        if self.emotional_state == "negative":
            adaptations['tone'] = "more supportive and understanding"
            adaptations['length'] = "longer, more thoughtful responses"
        elif self.emotional_state == "positive":
            adaptations['tone'] = "warm and encouraging"
            adaptations['energy'] = "higher"
        elif self.emotional_state == "concerned":
            adaptations['tone'] = "gentle and caring"
            adaptations['approach'] = "more empathetic"
        
        # Analyze conversation topics
        recent_topics = []
        for msg in conversation_history[-5:]:
            if msg['role'] == 'user':
                # Simple topic detection
                if any(word in msg['content'].lower() for word in ['relationship', 'love', 'feelings']):
                    recent_topics.append('relationship')
                elif any(word in msg['content'].lower() for word in ['work', 'job', 'career']):
                    recent_topics.append('work')
                elif any(word in msg['content'].lower() for word in ['family', 'parents', 'siblings']):
                    recent_topics.append('family')
        
        if 'relationship' in recent_topics:
            adaptations['focus'] = "relationship dynamics and emotional connection"
        elif 'work' in recent_topics:
            adaptations['focus'] = "professional life and ambitions"
        elif 'family' in recent_topics:
            adaptations['focus'] = "family relationships and personal history"
        
        self.personality_adaptations = adaptations
        return adaptations
    
    def generate_conversation_summary(self, conversation_history: List[Dict]) -> str:
        """Generate a brief summary of the conversation context."""
        if len(conversation_history) < 3:
            return "Beginning of conversation"
        
        # Extract key themes from recent messages
        recent_messages = conversation_history[-5:]
        themes = []
        
        for msg in recent_messages:
            content = msg['content'].lower()
            if any(word in content for word in ['relationship', 'love', 'feelings', 'together']):
                themes.append('relationship')
            elif any(word in content for word in ['work', 'job', 'career', 'future']):
                themes.append('future plans')
            elif any(word in content for word in ['family', 'parents', 'home']):
                themes.append('family')
            elif any(word in content for word in ['sorry', 'regret', 'mistake', 'wrong']):
                themes.append('apology/regret')
            elif any(word in content for word in ['miss', 'think about', 'remember']):
                themes.append('nostalgia')
        
        if themes:
            unique_themes = list(set(themes))
            return f"Recent topics: {', '.join(unique_themes)}"
        
        return f"Conversation in progress ({len(conversation_history)} messages)"
    
    def create_enhanced_system_prompt(self, analysis: Dict[str, Any], ghost_name: str, 
                                    conversation_history: List[Dict], user_message: str) -> str:
        """Create an enhanced system prompt with dynamic adaptations."""
        
        # Update emotional state and extract memories
        emotional_state = self.update_emotional_state(user_message, conversation_history)
        memory_items = self.extract_memory_items(user_message, conversation_history)
        personality_adaptations = self.adapt_personality(conversation_history, ghost_name)
        
        # Base personality from original analysis
        quirks_text = ", ".join(analysis['quirks']) if analysis['quirks'] else "no specific quirks detected"
        emojis_text = " ".join(analysis['top_emojis'][:3]) if analysis['top_emojis'] else "rarely uses emojis"
        
        # Dynamic adaptations text
        adaptations_text = ""
        if personality_adaptations:
            adaptations_text = f"\nCURRENT CONVERSATION ADAPTATIONS:\n"
            for key, value in personality_adaptations.items():
                adaptations_text += f"- {key}: {value}\n"
        
        # Memory context
        memory_text = ""
        if self.conversation_memory:
            recent_memories = self.conversation_memory[-5:]  # Last 5 memory items
            memory_text = f"\nIMPORTANT DETAILS TO REMEMBER:\n"
            for memory in recent_memories:
                memory_text += f"- {memory}\n"
        
        # Emotional state context
        emotional_context = f"\nCURRENT EMOTIONAL CONTEXT:\n- User's emotional state: {emotional_state}\n- Conversation depth: {len(conversation_history)} messages\n"
        
        # Conversation summary
        conversation_summary = self.generate_conversation_summary(conversation_history)
        context_summary = f"\nCONVERSATION CONTEXT:\n- {conversation_summary}\n"
        
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
{emotional_context}{adaptations_text}{memory_text}{context_summary}
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
9. MEMORY AWARENESS: Reference important details they've shared when relevant
10. EMOTIONAL ADAPTATION: Adjust your response style based on their current emotional state

Remember: You're simulating how {ghost_name} WOULD communicate if they were being honest and emotionally available. Match their style but with emotional depth appropriate to what the user is sharing."""
        
        return prompt
    
    def generate_response(self, messages: List[Dict], analysis: Dict, ghost_name: str) -> str:
        """Generate AI response based on conversation history with hybrid provider support."""
        
        # Check which provider is selected
        ai_provider = st.session_state.get('ai_provider', 'OpenAI (Advanced Features)')
        
        if "OpenAI" in ai_provider:
            # Try OpenAI first, fallback to Ollama if it fails
            openai_response = self._generate_openai_response(messages, analysis, ghost_name)
            if "Error" in openai_response or "API key" in openai_response:
                # Fallback to Ollama
                st.warning("🔄 OpenAI failed, switching to Ollama...")
                return self._generate_ollama_response(messages, analysis, ghost_name)
            return openai_response
        else:
            return self._generate_ollama_response(messages, analysis, ghost_name)
    
    def _generate_openai_response(self, messages: List[Dict], analysis: Dict, ghost_name: str) -> str:
        """Generate response using OpenAI with advanced features."""
        
        if not os.getenv("OPENAI_API_KEY"):
            return "⚠️ Please add your OpenAI API key in the sidebar to enable chat."
        
        try:
            # Get the latest user message for context
            latest_user_message = ""
            if messages:
                latest_user_message = messages[-1]['content'] if messages[-1]['role'] == 'user' else ""
            
            # Use enhanced system prompt with dynamic adaptations
            system_prompt = self.create_enhanced_system_prompt(
                analysis, ghost_name, messages, latest_user_message
            )
            
            # Build conversation history for context
            conversation = [{"role": "system", "content": system_prompt}]
            
            # Add last 10 messages for context
            for msg in messages[-10:]:
                conversation.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            # Enhanced API call with better parameters for dynamic responses
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                max_tokens=200,  # Increased for more thoughtful responses
                temperature=0.8,  # Slightly lower for more consistent personality
                presence_penalty=0.1,  # Encourage new topics
                frequency_penalty=0.1  # Reduce repetition
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ OpenAI Error: {str(e)}"
    
    def _generate_ollama_response(self, messages: List[Dict], analysis: Dict, ghost_name: str) -> str:
        """Generate response using Ollama with basic features."""
        
        try:
            # Use basic system prompt for Ollama
            system_prompt = self.create_system_prompt(analysis, ghost_name)
            
            # Build conversation history for context
            conversation = [{"role": "system", "content": system_prompt}]
            
            # Add last 10 messages for context
            for msg in messages[-10:]:
                conversation.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            # Get selected model
            selected_model = st.session_state.get('selected_model', DEFAULT_MODEL)
            
            # Ollama API call
            payload = {
                "model": selected_model,
                "messages": conversation,
                "stream": False,
                "options": {
                    "temperature": 0.9,
                    "num_predict": 150
                }
            }
            
            response = requests.post(f"{OLLAMA_ENDPOINT}/api/chat", json=payload)
            response.raise_for_status()
            
            return response.json()["message"]["content"]
            
        except requests.exceptions.ConnectionError:
            return "⚠️ Ollama is not running. Please start Ollama and ensure it's accessible at http://localhost:11434"
        except Exception as e:
            return f"❌ Ollama Error: {str(e)}"

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
        
        # AI Provider Selection
        st.markdown("**🤖 AI Provider**")
        ai_provider = st.radio(
            "Choose AI Provider:",
            ["OpenAI (Advanced Features)", "Ollama (Local & Private)"],
            help="OpenAI offers advanced features, Ollama runs locally"
        )
        
        # Store provider choice in session state
        if 'ai_provider' not in st.session_state:
            st.session_state.ai_provider = ai_provider
        else:
            st.session_state.ai_provider = ai_provider
        
        if "OpenAI" in ai_provider:
            # OpenAI Configuration
            st.markdown("**🔑 OpenAI Configuration**")
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=os.getenv("OPENAI_API_KEY", ""),
                help="Get your key from platform.openai.com"
            )
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
                openai.api_key = api_key
            
            # Show OpenAI features
            st.success("✅ Advanced Features Available:")
            st.caption("• Dynamic personality adaptation")
            st.caption("• Conversation memory system")
            st.caption("• Emotional state tracking")
            st.caption("• Context-aware responses")
            
        else:
            # Ollama Configuration
            st.markdown("**🏠 Ollama Configuration**")
            
            # Model selection
            selected_model = st.selectbox(
                "Choose Model:",
                AVAILABLE_MODELS,
                index=AVAILABLE_MODELS.index(DEFAULT_MODEL),
                help="Select the Ollama model to use for AI responses"
            )
            
            # Store selected model in session state
            if 'selected_model' not in st.session_state:
                st.session_state.selected_model = selected_model
            else:
                st.session_state.selected_model = selected_model
            
            st.caption(f"Endpoint: {OLLAMA_ENDPOINT}")
            
            # Check Ollama connection and available models
            try:
                response = requests.get(f"{OLLAMA_ENDPOINT}/api/tags", timeout=2)
                if response.status_code == 200:
                    available_models = [model['name'] for model in response.json()['models']]
                    if selected_model in available_models:
                        st.success(f"✅ {selected_model} is ready")
                    else:
                        st.warning(f"⚠️ {selected_model} not found")
                        st.caption(f"Run: `ollama pull {selected_model}`")
                else:
                    st.error("❌ Ollama connection failed")
            except:
                st.error("❌ Ollama is not running")
                st.caption("Start Ollama with: `ollama serve`")
            
            # Show Ollama features
            st.info("ℹ️ Basic Features Available:")
            st.caption("• Personality simulation")
            st.caption("• Local processing")
            st.caption("• No API costs")
            st.caption("• Complete privacy")
        
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
            
            # Advanced AI Features Status (OpenAI only)
            ai_provider = st.session_state.get('ai_provider', 'OpenAI (Advanced Features)')
            if "OpenAI" in ai_provider and hasattr(st.session_state.persona, 'emotional_state'):
                st.markdown("**🧠 Advanced AI Features Status**")
                
                col1, col2 = st.columns(2)
                with col1:
                    emotional_state = st.session_state.persona.emotional_state
                    state_emoji = {
                        "positive": "😊",
                        "negative": "😔", 
                        "concerned": "😟",
                        "hopeful": "😌",
                        "neutral": "😐"
                    }.get(emotional_state, "😐")
                    st.metric("Emotional State", f"{state_emoji} {emotional_state.title()}")
                
                with col2:
                    memory_count = len(st.session_state.persona.conversation_memory)
                    st.metric("Memories", f"{memory_count} items")
                
                # Show recent memories
                if st.session_state.persona.conversation_memory:
                    with st.expander("💭 Recent Memories"):
                        recent_memories = st.session_state.persona.conversation_memory[-5:]
                        for i, memory in enumerate(recent_memories, 1):
                            st.caption(f"{i}. {memory}")
                
                # Show personality adaptations
                if st.session_state.persona.personality_adaptations:
                    with st.expander("🎭 Current Adaptations"):
                        for key, value in st.session_state.persona.personality_adaptations.items():
                            st.caption(f"• {key}: {value}")
                
                st.markdown("---")
            elif "Ollama" in ai_provider:
                st.info("ℹ️ **Ollama Mode**: Basic personality simulation active")
                st.markdown("---")
            
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
                    ai_provider = st.session_state.get('ai_provider', 'OpenAI (Advanced Features)')
                    
                    with st.spinner("Writing..."):
                        try:
                            prompt = f"""Based on this chat analysis, write 2-3 compassionate paragraphs to help someone find closure.

Person: {st.session_state.ghost_name}
Total messages: {analysis['total_messages']}
Their average message length: {analysis['avg_words']} words
Emotional tone: {analysis['tone']}
Sentiment score: {analysis['avg_sentiment']}

Write gentle, honest observations about their communication style. Be compassionate but truthful. Help them understand and find peace."""

                            if "OpenAI" in ai_provider:
                                if not os.getenv("OPENAI_API_KEY"):
                                    st.error("Please add your OpenAI API key above.")
                                else:
                                    response = openai.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[{"role": "user", "content": prompt}],
                                        max_tokens=400,
                                        temperature=0.7
                                    )
                                    st.write(response.choices[0].message.content)
                            else:
                                # Ollama closure letter
                                selected_model = st.session_state.get('selected_model', DEFAULT_MODEL)
                                payload = {
                                    "model": selected_model,
                                    "messages": [{"role": "user", "content": prompt}],
                                    "stream": False,
                                    "options": {
                                        "temperature": 0.7,
                                        "num_predict": 400
                                    }
                                }
                                
                                response = requests.post(f"{OLLAMA_ENDPOINT}/api/chat", json=payload)
                                response.raise_for_status()
                                st.write(response.json()["message"]["content"])
                                
                        except requests.exceptions.ConnectionError:
                            st.error("⚠️ Ollama is not running. Please start Ollama.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            st.markdown("---")
            
            # Conversation Export
            with st.expander("💾 Export Conversation"):
                if st.button("📄 Export as Text"):
                    if st.session_state.chat_history:
                        # Create export content
                        export_content = f"GhostBack.ai Conversation Export\n"
                        export_content += f"Person: {st.session_state.ghost_name}\n"
                        export_content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                        export_content += f"Total Messages: {len(st.session_state.chat_history)}\n\n"
                        
                        for i, msg in enumerate(st.session_state.chat_history, 1):
                            role = "You" if msg['role'] == 'user' else st.session_state.ghost_name
                            export_content += f"{i}. {role}: {msg['content']}\n\n"
                        
                        # Add AI analysis summary
                        if hasattr(st.session_state.persona, 'emotional_state'):
                            export_content += f"\n--- AI Analysis Summary ---\n"
                            export_content += f"Final Emotional State: {st.session_state.persona.emotional_state}\n"
                            export_content += f"Memories Captured: {len(st.session_state.persona.conversation_memory)}\n"
                            if st.session_state.persona.personality_adaptations:
                                export_content += f"Personality Adaptations: {st.session_state.persona.personality_adaptations}\n"
                        
                        st.download_button(
                            label="Download Conversation",
                            data=export_content,
                            file_name=f"ghostback_conversation_{st.session_state.ghost_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.info("No conversation to export yet.")
            
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