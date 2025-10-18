"""
Core business logic for GhostBack.ai API
Extracted from app.py for reuse
"""

import re
import openai
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple


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
    
    def identify_participants(self, messages: List[Dict[str, str]]) -> Tuple[Optional[str], Optional[str]]:
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
            return "Please add your OpenAI API key to enable chat."
        
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
            return f"Error: {str(e)}"
    
    def generate_closure_letter(self, analysis: Dict[str, Any], ghost_name: str) -> str:
        """Generate a closure letter based on analysis."""
        
        if not os.getenv("OPENAI_API_KEY"):
            return "Please add your OpenAI API key to generate closure letter."
        
        try:
            prompt = f"""Based on this chat analysis, write 2-3 compassionate paragraphs to help someone find closure.

Person: {ghost_name}
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
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error: {str(e)}"
