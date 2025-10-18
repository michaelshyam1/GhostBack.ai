"""
Emotional Safety Analyzer for GhostBack.ai
Monitors conversation intensity and provides warnings for emotional overload
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
import openai
import os
from datetime import datetime, timedelta


class EmotionalSafetyAnalyzer:
    """Analyzes conversation for emotional safety and provides warnings."""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.warning_thresholds = {
            'high_negativity': -0.6,  # Very negative sentiment
            'intense_emotion': 0.8,   # High emotional intensity
            'rapid_escalation': 0.3,  # Quick sentiment change
            'vulnerability_indicators': 3,  # Number of vulnerable phrases
            'message_frequency': 5,   # Messages per minute
            'session_duration': 30,   # Minutes before suggesting breaks
        }
        
        # Phrases that indicate high emotional vulnerability
        self.vulnerability_indicators = [
            r'\b(i can\'t|can\'t|cannot)\b',
            r'\b(always|never)\b',
            r'\b(why did|why didn\'t)\b',
            r'\b(i hate|hate)\b',
            r'\b(i wish|wish)\b',
            r'\b(if only|only if)\b',
            r'\b(should have|shouldn\'t have)\b',
            r'\b(regret|regrets)\b',
            r'\b(blame|blaming)\b',
            r'\b(guilt|guilty)\b',
            r'\b(worthless|useless)\b',
            r'\b(hopeless|hopelessness)\b',
            r'\b(alone|lonely)\b',
            r'\b(abandoned|abandon)\b',
            r'\b(betrayed|betrayal)\b',
            r'\b(heartbroken|broken)\b',
            r'\b(devastated|devastating)\b',
            r'\b(can\'t go on|give up)\b',
            r'\b(end it all|end myself)\b',
            r'\b(not worth it|not worth living)\b',
        ]
        
        # Crisis indicators that require immediate attention
        self.crisis_indicators = [
            r'\b(kill myself|kill me)\b',
            r'\b(end my life|end it all)\b',
            r'\b(suicide|suicidal)\b',
            r'\b(not worth living|not worth it)\b',
            r'\b(want to die|wanna die)\b',
            r'\b(no point|pointless)\b',
            r'\b(permanent solution|permanent fix)\b',
            r'\b(never wake up|never wake)\b',
        ]
    
    def analyze_message_safety(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze a single message for emotional safety indicators."""
        
        message_lower = message.lower()
        
        # Basic sentiment analysis
        sentiment = self.sentiment_analyzer.polarity_scores(message)
        
        # Check for vulnerability indicators
        vulnerability_count = 0
        for pattern in self.vulnerability_indicators:
            if re.search(pattern, message_lower, re.IGNORECASE):
                vulnerability_count += 1
        
        # Check for crisis indicators
        crisis_detected = False
        crisis_phrases = []
        for pattern in self.crisis_indicators:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            if matches:
                crisis_detected = True
                crisis_phrases.extend(matches)
        
        # Calculate emotional intensity
        emotional_intensity = abs(sentiment['compound'])
        
        # Check for rapid escalation (if context provided)
        rapid_escalation = False
        if context and 'previous_sentiment' in context:
            sentiment_change = abs(sentiment['compound'] - context['previous_sentiment'])
            rapid_escalation = sentiment_change > self.warning_thresholds['rapid_escalation']
        
        # Determine warning level
        warning_level = "none"
        warnings = []
        
        if crisis_detected:
            warning_level = "crisis"
            warnings.append({
                "type": "crisis",
                "message": "Crisis indicators detected. Please seek immediate professional help.",
                "phrases": crisis_phrases,
                "urgency": "immediate"
            })
        elif vulnerability_count >= self.warning_thresholds['vulnerability_indicators']:
            warning_level = "high"
            warnings.append({
                "type": "high_vulnerability",
                "message": "High emotional vulnerability detected. Consider taking a break.",
                "count": vulnerability_count,
                "urgency": "high"
            })
        elif emotional_intensity > self.warning_thresholds['intense_emotion']:
            warning_level = "medium"
            warnings.append({
                "type": "intense_emotion",
                "message": "Intense emotions detected. Remember to breathe and take care of yourself.",
                "intensity": emotional_intensity,
                "urgency": "medium"
            })
        elif rapid_escalation:
            warning_level = "medium"
            warnings.append({
                "type": "rapid_escalation",
                "message": "Emotional intensity is escalating quickly. Consider pausing the conversation.",
                "change": sentiment_change,
                "urgency": "medium"
            })
        elif sentiment['compound'] < self.warning_thresholds['high_negativity']:
            warning_level = "low"
            warnings.append({
                "type": "high_negativity",
                "message": "You're experiencing very negative emotions. Remember this is temporary.",
                "sentiment": sentiment['compound'],
                "urgency": "low"
            })
        
        return {
            "warning_level": warning_level,
            "warnings": warnings,
            "sentiment": sentiment,
            "vulnerability_count": vulnerability_count,
            "crisis_detected": crisis_detected,
            "emotional_intensity": emotional_intensity,
            "rapid_escalation": rapid_escalation,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_conversation_safety(self, chat_history: List[Dict[str, str]], session_start: datetime = None) -> Dict[str, Any]:
        """Analyze entire conversation for safety patterns."""
        
        if not chat_history:
            return {"warning_level": "none", "warnings": []}
        
        # Analyze each user message
        user_messages = [msg for msg in chat_history if msg.get('role') == 'user']
        safety_analyses = []
        
        for i, message in enumerate(user_messages):
            context = {}
            if i > 0 and safety_analyses:
                context['previous_sentiment'] = safety_analyses[-1]['sentiment']['compound']
            
            analysis = self.analyze_message_safety(message['content'], context)
            safety_analyses.append(analysis)
        
        # Check for session duration warnings
        session_warnings = []
        if session_start:
            session_duration = (datetime.now() - session_start).total_seconds() / 60
            if session_duration > self.warning_thresholds['session_duration']:
                session_warnings.append({
                    "type": "long_session",
                    "message": f"You've been in this conversation for {session_duration:.1f} minutes. Consider taking a break.",
                    "duration_minutes": session_duration,
                    "urgency": "low"
                })
        
        # Check for message frequency
        if len(user_messages) > 10:  # Only check if there are enough messages
            recent_messages = user_messages[-5:]  # Last 5 messages
            if len(recent_messages) >= 5:
                # Estimate frequency (simplified)
                frequency_warnings = []
                if len(recent_messages) >= self.warning_thresholds['message_frequency']:
                    frequency_warnings.append({
                        "type": "high_frequency",
                        "message": "You're sending messages very quickly. Slow down and breathe.",
                        "urgency": "medium"
                    })
        
        # Aggregate warnings
        all_warnings = []
        max_warning_level = "none"
        
        for analysis in safety_analyses:
            all_warnings.extend(analysis['warnings'])
            if analysis['warning_level'] == 'crisis':
                max_warning_level = 'crisis'
            elif analysis['warning_level'] == 'high' and max_warning_level != 'crisis':
                max_warning_level = 'high'
            elif analysis['warning_level'] == 'medium' and max_warning_level not in ['crisis', 'high']:
                max_warning_level = 'medium'
            elif analysis['warning_level'] == 'low' and max_warning_level == 'none':
                max_warning_level = 'low'
        
        all_warnings.extend(session_warnings)
        all_warnings.extend(frequency_warnings if 'frequency_warnings' in locals() else [])
        
        return {
            "warning_level": max_warning_level,
            "warnings": all_warnings,
            "total_messages": len(user_messages),
            "safety_analyses": safety_analyses,
            "session_duration_minutes": (datetime.now() - session_start).total_seconds() / 60 if session_start else 0
        }
    
    def generate_safety_recommendation(self, analysis: Dict[str, Any]) -> str:
        """Generate a personalized safety recommendation based on analysis."""
        
        if analysis['warning_level'] == 'crisis':
            return """IMMEDIATE SUPPORT NEEDED

I'm concerned about your safety. Please:
1. Call a crisis helpline immediately (988 in US, or your local emergency number)
2. Reach out to a trusted friend or family member
3. Consider speaking with a mental health professional
4. Remember: You are not alone, and this feeling will pass

This conversation can wait. Your safety comes first."""
        
        elif analysis['warning_level'] == 'high':
            return """EMOTIONAL OVERLOAD DETECTED

You're experiencing intense emotions right now. Please:
1. Take a deep breath and step away from this conversation
2. Do something calming (walk, music, call a friend)
3. Consider talking to someone you trust about how you're feeling
4. Return to this conversation when you feel more centered

Your emotional well-being is important."""
        
        elif analysis['warning_level'] == 'medium':
            return """GENTLE REMINDER

I notice you're feeling very emotional. Remember to:
1. Take breaks when you need them
2. Practice self-care
3. Stay hydrated and take care of your basic needs
4. Know that it's okay to pause this conversation anytime

You're doing important work, but your well-being matters most."""
        
        else:
            return """YOU'RE DOING WELL

You're handling this conversation with care and thoughtfulness. Keep taking it at your own pace, and remember to be gentle with yourself."""
    
    def should_pause_conversation(self, analysis: Dict[str, Any]) -> bool:
        """Determine if the conversation should be paused for safety."""
        return analysis['warning_level'] in ['crisis', 'high']
    
    def get_crisis_resources(self) -> List[Dict[str, str]]:
        """Get crisis resources for immediate help."""
        return [
            {
                "name": "National Suicide Prevention Lifeline",
                "number": "988",
                "description": "24/7 crisis support"
            },
            {
                "name": "Crisis Text Line",
                "number": "Text HOME to 741741",
                "description": "24/7 crisis text support"
            },
            {
                "name": "International Association for Suicide Prevention",
                "url": "https://www.iasp.info/resources/Crisis_Centres/",
                "description": "Global crisis resources"
            }
        ]
