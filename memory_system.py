"""
Replay Memory System for GhostBack.ai
Allows AI to reference specific past conversations and events from chat history
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import openai

class MemorySystem:
    """Manages and retrieves memories from original chat history."""
    
    def __init__(self, messages: List[Dict[str, str]], ghost_name: str):
        """
        Initialize with parsed chat messages.
        
        Args:
            messages: List of parsed messages with 'text', 'sender', 'timestamp'
            ghost_name: Name of the person being simulated
        """
        self.all_messages = messages
        self.ghost_name = ghost_name
        self.ghost_messages = [msg for msg in messages if msg['sender'] == ghost_name]
        self.indexed_memories = self._create_memory_index()
    
    def _create_memory_index(self) -> Dict[str, List[Dict]]:
        """Create searchable index of conversation topics and events."""
        index = {
            'locations': [],
            'events': [],
            'emotions': [],
            'questions': [],
            'all_exchanges': []
        }
        
        # Keywords for different categories
        location_keywords = ['at', 'in', 'to', 'from', 'trip', 'visit', 'restaurant', 'cafe', 'park', 'home', 'beach']
        event_keywords = ['party', 'dinner', 'lunch', 'movie', 'concert', 'trip', 'visit', 'meeting', 'date', 'birthday']
        emotion_keywords = ['love', 'hate', 'happy', 'sad', 'angry', 'sorry', 'miss', 'excited', 'nervous', 'worried']
        
        # Index messages with context (previous and next messages)
        for i, msg in enumerate(self.all_messages):
            # Get context window (2 messages before and after)
            context_start = max(0, i - 2)
            context_end = min(len(self.all_messages), i + 3)
            context = self.all_messages[context_start:context_end]
            
            text_lower = msg['text'].lower()
            
            # Create memory entry with context
            memory_entry = {
                'message': msg,
                'index': i,
                'context': context,
                'context_text': self._format_context(context)
            }
            
            # Categorize by keywords
            if any(keyword in text_lower for keyword in location_keywords):
                index['locations'].append(memory_entry)
            
            if any(keyword in text_lower for keyword in event_keywords):
                index['events'].append(memory_entry)
            
            if any(keyword in text_lower for keyword in emotion_keywords):
                index['emotions'].append(memory_entry)
            
            # Questions (ending with ?)
            if '?' in msg['text']:
                index['questions'].append(memory_entry)
            
            # Store all exchanges (for general search)
            index['all_exchanges'].append(memory_entry)
        
        return index
    
    def _format_context(self, messages: List[Dict]) -> str:
        """Format a sequence of messages as readable context."""
        formatted = []
        for msg in messages:
            formatted.append(f"{msg['sender']}: {msg['text']}")
        return "\n".join(formatted)
    
    def search_memories(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for relevant memories based on a query.
        
        Args:
            query: User's question or statement
            top_k: Number of top memories to return
            
        Returns:
            List of relevant memory entries with context
        """
        query_lower = query.lower()
        scored_memories = []
        
        # Simple keyword-based scoring (can be upgraded to embeddings later)
        for memory in self.indexed_memories['all_exchanges']:
            score = 0
            text_lower = memory['message']['text'].lower()
            
            # Exact phrase match
            if query_lower in text_lower:
                score += 10
            
            # Word overlap
            query_words = set(re.findall(r'\b\w+\b', query_lower))
            text_words = set(re.findall(r'\b\w+\b', text_lower))
            overlap = len(query_words & text_words)
            score += overlap * 2
            
            # Check context too
            context_lower = memory['context_text'].lower()
            if query_lower in context_lower:
                score += 5
            
            # Boost if it's from the ghost
            if memory['message']['sender'] == self.ghost_name:
                score += 3
            
            if score > 0:
                scored_memories.append((score, memory))
        
        # Sort by score and return top K
        scored_memories.sort(reverse=True, key=lambda x: x[0])
        return [mem for score, mem in scored_memories[:top_k]]
    
    def get_memories_by_category(self, category: str, limit: int = 5) -> List[Dict]:
        """Get memories from a specific category."""
        if category in self.indexed_memories:
            return self.indexed_memories[category][:limit]
        return []
    
    def find_memory_around_time(self, reference: str) -> Optional[Dict]:
        """Find memories around a time reference like 'after our trip' or 'last week'."""
        # This is a simplified version - could be enhanced with actual date parsing
        reference_lower = reference.lower()
        
        # Look for time-related keywords
        time_keywords = ['after', 'before', 'during', 'when', 'last', 'trip', 'weekend']
        
        for keyword in time_keywords:
            if keyword in reference_lower:
                memories = self.search_memories(reference, top_k=1)
                if memories:
                    return memories[0]
        
        return None
    
    def format_memory_for_prompt(self, memories: List[Dict]) -> str:
        """Format retrieved memories for inclusion in AI prompt."""
        if not memories:
            return ""
        
        formatted = "\n\nRELEVANT PAST CONVERSATIONS:\n"
        for i, mem in enumerate(memories, 1):
            formatted += f"\n--- Memory {i} ({mem['message']['timestamp']}) ---\n"
            formatted += mem['context_text']
            formatted += "\n"
        
        return formatted
    
    def detect_memory_query(self, user_message: str) -> bool:
        """
        Detect if user is asking about past events/conversations.
        
        Returns True if message contains memory-related questions.
        """
        memory_patterns = [
            r'\bwhy did (you|we)\b',
            r'\bremember when\b',
            r'\bwhat happened\b',
            r'\bafter (our|the|that)\b',
            r'\bbefore (our|the|that)\b',
            r'\bthat time when\b',
            r'\byou (said|told|mentioned)\b',
            r'\bwhat about\b',
            r'\blast (time|week|month)\b'
        ]
        
        message_lower = user_message.lower()
        return any(re.search(pattern, message_lower) for pattern in memory_patterns)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get overview statistics about the conversation."""
        return {
            'total_messages': len(self.all_messages),
            'ghost_messages': len(self.ghost_messages),
            'total_events': len(self.indexed_memories['events']),
            'total_questions': len(self.indexed_memories['questions']),
            'first_message': self.all_messages[0] if self.all_messages else None,
            'last_message': self.all_messages[-1] if self.all_messages else None
        }


class EnhancedAIPersona:
    """Enhanced AI Persona with memory retrieval capabilities."""
    
    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system
    
    def create_system_prompt_with_memory(self, analysis: Dict[str, Any], 
                                         ghost_name: str, 
                                         relevant_memories: str = "") -> str:
        """Create system prompt that includes memory context."""
        
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

{relevant_memories}

RULES:
1. If the user asks about past events, reference the RELEVANT PAST CONVERSATIONS above
2. Answer from {ghost_name}'s perspective based on what actually happened in your chat history
3. Keep responses in their texting style - short, casual, using their words
4. Don't make up events that aren't in the memories
5. If you don't remember something, say so naturally ("idk" or "can't remember tbh")

You are {ghost_name}. Answer honestly based on your real conversations."""
        
        return prompt
    
    def generate_response_with_memory(self, messages: List[Dict], 
                                     analysis: Dict, 
                                     ghost_name: str,
                                     user_message: str) -> str:
        """Generate AI response with memory retrieval."""
        
        if not openai.api_key:
            return "⚠️ OpenAI API key not configured."
        
        try:
            # Check if this is a memory-related query
            is_memory_query = self.memory_system.detect_memory_query(user_message)
            
            relevant_memories = ""
            if is_memory_query:
                # Retrieve relevant memories
                memories = self.memory_system.search_memories(user_message, top_k=3)
                relevant_memories = self.memory_system.format_memory_for_prompt(memories)
            
            # Create enhanced system prompt
            system_prompt = self.create_system_prompt_with_memory(
                analysis, ghost_name, relevant_memories
            )
            
            conversation = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in messages[-8:]:
                conversation.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            # Adjust token limit
            target_tokens = int(analysis['avg_words'] * 5)
            max_response_tokens = max(60, min(target_tokens, 200)) if is_memory_query else max(40, min(target_tokens, 150))
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                max_tokens=max_response_tokens,
                temperature=0.85
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error: {str(e)}"