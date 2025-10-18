import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
import openai
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Page configuration
st.set_page_config(
    page_title="GhostBack.ai",
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
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
    }
    .disclaimer {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 1rem;
        max-width: 80%;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
    }
    .ai-message {
        background-color: #f8f9fa;
        color: #333;
        margin-right: auto;
    }
</style>
""", unsafe_allow_html=True)

class ChatAnalyzer:
    """Analyzes chat history to extract conversational patterns and style."""
    
    def __init__(self):
        self.patterns = {}
    
    def analyze_chat_file(self, file_content: str) -> Dict[str, Any]:
        """Analyze uploaded chat file and extract conversational patterns."""
        try:
            # Parse different file formats
            if file_content.startswith('[') or file_content.startswith('{'):
                # JSON format
                data = json.loads(file_content)
                messages = self._extract_messages_from_json(data)
            else:
                # Text format - try to parse common chat formats
                messages = self._extract_messages_from_text(file_content)
            
            if not messages:
                # Debug information
                lines = file_content.split('\n')[:5]  # First 5 lines for debugging
                return {
                    "error": "No messages found in the uploaded file",
                    "debug_info": {
                        "file_length": len(file_content),
                        "first_few_lines": lines,
                        "file_starts_with": file_content[:50] if len(file_content) > 50 else file_content
                    }
                }
            
            # Analyze conversational patterns
            analysis = {
                "total_messages": len(messages),
                "conversation_style": self._analyze_conversation_style(messages),
                "common_phrases": self._extract_common_phrases(messages),
                "response_patterns": self._analyze_response_patterns(messages),
                "emotional_tone": self._analyze_emotional_tone(messages),
                "message_length_stats": self._analyze_message_lengths(messages)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Error analyzing chat file: {str(e)}"}
    
    def _extract_messages_from_json(self, data: Any) -> List[Dict[str, str]]:
        """Extract messages from JSON data."""
        messages = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if 'message' in item and 'sender' in item:
                        messages.append({
                            'text': item['message'],
                            'sender': item['sender'],
                            'timestamp': item.get('timestamp', '')
                        })
                    elif 'content' in item and 'author' in item:
                        messages.append({
                            'text': item['content'],
                            'sender': item['author'],
                            'timestamp': item.get('timestamp', '')
                        })
        
        return messages
    
    def _extract_messages_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract messages from plain text format."""
        messages = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to match common chat patterns
            # Format: [timestamp] sender: message
            timestamp_pattern = r'\[([^\]]+)\]\s*([^:]+):\s*(.*)'
            match = re.match(timestamp_pattern, line)
            
            if match:
                messages.append({
                    'text': match.group(3).strip(),
                    'sender': match.group(2).strip(),
                    'timestamp': match.group(1).strip()
                })
            else:
                # Try format: sender: message (without timestamp)
                colon_pattern = r'^([^:]+):\s*(.*)'
                match = re.match(colon_pattern, line)
                if match:
                    messages.append({
                        'text': match.group(2).strip(),
                        'sender': match.group(1).strip(),
                        'timestamp': ''
                    })
        
        return messages
    
    def _analyze_conversation_style(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze the overall conversation style."""
        if not messages:
            return {}
        
        # Find the ghost's messages (assuming they're not the user)
        ghost_messages = [msg for msg in messages if msg['sender'].lower() not in ['me', 'user', 'you']]
        
        if not ghost_messages:
            return {"error": "Could not identify ghost's messages"}
        
        # Analyze writing patterns
        avg_length = sum(len(msg['text']) for msg in ghost_messages) / len(ghost_messages)
        
        # Common sentence starters
        starters = []
        for msg in ghost_messages:
            first_word = msg['text'].split()[0].lower() if msg['text'].split() else ""
            if first_word:
                starters.append(first_word)
        
        # Most common punctuation
        punctuation = []
        for msg in ghost_messages:
            for char in msg['text']:
                if char in '!?.,;:':
                    punctuation.append(char)
        
        return {
            "average_message_length": round(avg_length, 2),
            "common_starters": self._get_most_common(starters, 5),
            "common_punctuation": self._get_most_common(punctuation, 5),
            "message_count": len(ghost_messages)
        }
    
    def _extract_common_phrases(self, messages: List[Dict[str, str]]) -> List[str]:
        """Extract commonly used phrases."""
        ghost_messages = [msg for msg in messages if msg['sender'].lower() not in ['me', 'user', 'you']]
        
        if not ghost_messages:
            return []
        
        # Extract 2-3 word phrases
        phrases = []
        for msg in ghost_messages:
            words = msg['text'].lower().split()
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                phrases.append(phrase)
        
        return self._get_most_common(phrases, 10)
    
    def _analyze_response_patterns(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze response patterns and timing."""
        # This would analyze response times, message frequency, etc.
        return {
            "response_consistency": "analyzed",
            "message_frequency": "analyzed"
        }
    
    def _analyze_emotional_tone(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze emotional tone of messages."""
        ghost_messages = [msg for msg in messages if msg['sender'].lower() not in ['me', 'user', 'you']]
        
        if not ghost_messages:
            return {}
        
        # Simple sentiment analysis based on common words
        positive_words = ['good', 'great', 'awesome', 'amazing', 'love', 'happy', 'excited', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'sad', 'angry', 'frustrated', 'disappointed']
        
        positive_count = 0
        negative_count = 0
        
        for msg in ghost_messages:
            text = msg['text'].lower()
            for word in positive_words:
                positive_count += text.count(word)
            for word in negative_words:
                negative_count += text.count(word)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            sentiment_ratio = positive_count / total_sentiment_words
        else:
            sentiment_ratio = 0.5
        
        return {
            "sentiment_ratio": round(sentiment_ratio, 2),
            "overall_tone": "positive" if sentiment_ratio > 0.6 else "negative" if sentiment_ratio < 0.4 else "neutral"
        }
    
    def _analyze_message_lengths(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze message length patterns."""
        ghost_messages = [msg for msg in messages if msg['sender'].lower() not in ['me', 'user', 'you']]
        
        if not ghost_messages:
            return {}
        
        lengths = [len(msg['text']) for msg in ghost_messages]
        
        return {
            "average_length": round(sum(lengths) / len(lengths), 2),
            "shortest": min(lengths),
            "longest": max(lengths),
            "length_variation": round(max(lengths) - min(lengths), 2)
        }
    
    def _get_most_common(self, items: List[str], n: int) -> List[str]:
        """Get the most common items from a list."""
        from collections import Counter
        return [item for item, count in Counter(items).most_common(n)]

class AIPersonaGenerator:
    """Generates AI persona based on analyzed chat patterns."""
    
    def __init__(self):
        self.openai_client = openai
    
    def generate_persona_prompt(self, analysis: Dict[str, Any]) -> str:
        """Generate a prompt for creating the AI persona."""
        if "error" in analysis:
            return "Error in analysis"
        
        style = analysis.get("conversation_style", {})
        phrases = analysis.get("common_phrases", [])
        tone = analysis.get("emotional_tone", {})
        length_stats = analysis.get("message_length_stats", {})
        
        # Extract more detailed patterns
        common_starters = style.get('common_starters', [])[:5]
        common_punctuation = style.get('common_punctuation', [])[:5]
        avg_length = style.get('average_message_length', 0)
        overall_tone = tone.get('overall_tone', 'neutral')
        sentiment_ratio = tone.get('sentiment_ratio', 0.5)
        
        prompt = f"""You are an AI simulation designed to help someone process emotional closure. Based on the analyzed chat patterns, you should respond as if you were the person from the chat history, but you are clearly an AI simulation for therapeutic purposes.

CONVERSATIONAL STYLE TO MATCH:
- Average message length: {avg_length} characters
- Common ways to start messages: {', '.join(common_starters) if common_starters else 'not specified'}
- Common punctuation patterns: {', '.join(common_punctuation) if common_punctuation else 'not specified'}
- Overall emotional tone: {overall_tone} (sentiment ratio: {sentiment_ratio})
- Common phrases you used: {', '.join(phrases[:8]) if phrases else 'not available'}

IMPORTANT GUIDELINES:
1. Respond in a similar style to the analyzed patterns - use similar sentence structures, length, and tone
2. Incorporate the common phrases naturally when appropriate
3. Match the emotional tone and communication style
4. Be empathetic and understanding, as this is for closure and healing
5. ALWAYS start responses with "As an AI simulation based on your chat analysis, I..." or similar to make it clear you're not the real person
6. Help the user process their emotions and find closure
7. Be honest about being an AI simulation while still being helpful for therapeutic purposes
8. Use the analyzed communication patterns to make responses feel authentic to the original person's style

Remember: You are helping someone find closure and process difficult emotions through AI-assisted reflection. Be kind, understanding, and authentic to the analyzed communication style while being clear about your AI nature."""
        
        return prompt
    
    def generate_response(self, user_message: str, analysis: Dict[str, Any]) -> str:
        """Generate a response using the AI persona."""
        if not os.getenv("OPENAI_API_KEY"):
            return "OpenAI API key not configured. Please set OPENAI_API_KEY in your environment variables."
        
        try:
            persona_prompt = self.generate_persona_prompt(analysis)
            
            # Create a more conversational context
            conversation_context = f"""Based on the analyzed chat patterns, respond to this message as the AI simulation of the person from the chat history.

User's message: "{user_message}"

Remember to:
- Match the conversational style from the analysis
- Use similar phrases and patterns when appropriate
- Be empathetic and helpful for closure
- Clearly identify as an AI simulation
- Keep responses authentic to the analyzed communication style"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": persona_prompt},
                    {"role": "user", "content": conversation_context}
                ],
                max_tokens=300,
                temperature=0.8
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"

def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">👻 GhostBack.ai</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Find closure through AI-assisted reflection</p>', unsafe_allow_html=True)
    
    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
    <strong>⚠️ Important Disclaimer:</strong> This application creates an AI simulation based on uploaded chat history. 
    It is designed for personal reflection and emotional closure, not to impersonate real people. 
    The AI persona is clearly identified as a simulation and should be used responsibly for therapeutic purposes only.
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None
    if 'persona_generator' not in st.session_state:
        st.session_state.persona_generator = AIPersonaGenerator()
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ChatAnalyzer()
    
    # Sidebar for file upload and analysis
    with st.sidebar:
        st.header("📁 Upload Chat History")
        
        uploaded_file = st.file_uploader(
            "Choose a chat history file",
            type=['txt', 'json'],
            help="Upload a text file or JSON file containing your chat history"
        )
        
        if uploaded_file is not None:
            file_content = uploaded_file.read().decode('utf-8')
            
            if st.button("Analyze Chat History"):
                with st.spinner("Analyzing chat patterns..."):
                    analysis = st.session_state.analyzer.analyze_chat_file(file_content)
                    st.session_state.analysis = analysis
                
                if "error" in analysis:
                    st.error(analysis["error"])
                    if "debug_info" in analysis:
                        st.write("Debug information:")
                        st.json(analysis["debug_info"])
                else:
                    st.success("Chat analysis complete!")
                    
                    # Display key analysis results in a more readable format
                    st.subheader("Analysis Results")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total Messages", analysis.get("total_messages", 0))
                        
                        style = analysis.get("conversation_style", {})
                        st.metric("Avg Message Length", f"{style.get('average_message_length', 0):.0f} chars")
                        
                        tone = analysis.get("emotional_tone", {})
                        st.metric("Overall Tone", tone.get("overall_tone", "Unknown").title())
                    
                    with col2:
                        phrases = analysis.get("common_phrases", [])
                        if phrases:
                            st.write("**Common Phrases:**")
                            for phrase in phrases[:5]:
                                st.write(f"• {phrase}")
                        
                        starters = style.get("common_starters", [])
                        if starters:
                            st.write("**Common Starters:**")
                            st.write(", ".join(starters[:3]))
                    
                    # Show full analysis in expander
                    with st.expander("View Full Analysis"):
                        st.json(analysis)
        
        # API Key configuration
        st.header("🔑 Configuration")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key to enable AI responses"
        )
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("API key configured!")
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat with AI Persona")
        
        if st.session_state.analysis and "error" not in st.session_state.analysis:
            # Show analysis summary for context
            analysis = st.session_state.analysis
            style = analysis.get("conversation_style", {})
            tone = analysis.get("emotional_tone", {})
            
            st.info(f"🤖 **AI Persona Active** - Simulating based on {analysis.get('total_messages', 0)} messages with {tone.get('overall_tone', 'neutral')} tone and {style.get('average_message_length', 0):.0f} char average message length")
            
            # Chat interface
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f'<div class="chat-message user-message">{message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message ai-message">{message["content"]}</div>', unsafe_allow_html=True)
            
            # Message input
            user_input = st.text_input("Type your message here...", key="user_input")
            
            if st.button("Send") and user_input:
                # Add user message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Generate AI response
                with st.spinner("AI is analyzing patterns and generating response..."):
                    ai_response = st.session_state.persona_generator.generate_response(
                        user_input, 
                        st.session_state.analysis
                    )
                
                # Add AI response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                st.rerun()
            
            # Clear chat button
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        else:
            st.info("Please upload and analyze a chat history file to begin.")
    
    with col2:
        st.header("📊 Analysis Summary")
        
        if st.session_state.analysis and "error" not in st.session_state.analysis:
            analysis = st.session_state.analysis
            
            st.metric("Total Messages", analysis.get("total_messages", 0))
            
            style = analysis.get("conversation_style", {})
            st.metric("Avg Message Length", f"{style.get('average_message_length', 0)} chars")
            
            tone = analysis.get("emotional_tone", {})
            st.metric("Overall Tone", tone.get("overall_tone", "Unknown").title())
            
            # Common phrases
            phrases = analysis.get("common_phrases", [])
            if phrases:
                st.subheader("Common Phrases")
                for phrase in phrases[:5]:
                    st.write(f"• {phrase}")
        
        else:
            st.info("Upload a chat file to see analysis results here.")

if __name__ == "__main__":
    main()
