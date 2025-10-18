#!/usr/bin/env python3
"""
Example client for GhostBack.ai API
Demonstrates how to use the API endpoints
"""

import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def analyze_chat(chat_text: str, ghost_name: str = None) -> Dict[str, Any]:
    """Analyze chat history."""
    print("📊 Analyzing chat history...")
    
    payload = {
        "chat_text": chat_text,
        "ghost_name": ghost_name
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    result = response.json()
    
    if result["success"]:
        print(f"✅ Analysis successful!")
        print(f"Participants: {result['participants']}")
        print(f"Analysis: {json.dumps(result['analysis'], indent=2)}")
    else:
        print(f"❌ Analysis failed: {result['message']}")
    
    return result

def chat_with_persona(message: str, analysis_data: Dict[str, Any], session_id: str = None) -> str:
    """Chat with the AI persona."""
    print(f"💬 Sending message: {message}")
    
    payload = {
        "message": message,
        "session_id": session_id,
        "analysis_data": analysis_data
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    result = response.json()
    
    if result["success"]:
        print(f"🤖 AI Response: {result['message']}")
        return result["session_id"]
    else:
        print(f"❌ Chat failed: {result['message']}")
        return None

def generate_closure_letter(analysis_data: Dict[str, Any], ghost_name: str) -> str:
    """Generate a closure letter."""
    print("📝 Generating closure letter...")
    
    payload = {
        "analysis_data": analysis_data,
        "ghost_name": ghost_name
    }
    
    response = requests.post(f"{BASE_URL}/closure-letter", json=payload)
    result = response.json()
    
    if result["success"]:
        print(f"✅ Closure letter generated!")
        print(f"Letter: {result['letter']}")
        return result["letter"]
    else:
        print(f"❌ Failed to generate letter: {result['error']}")
        return None

def main():
    """Example usage of the API."""
    print("👻 GhostBack.ai API Client Example")
    print("=" * 50)
    
    # Test health
    test_health()
    
    # Sample chat data
    sample_chat = """[1/15/24, 10:30 PM] Alex: hey what's up
[1/15/24, 10:32 PM] Jordan: not much haha
[1/15/24, 10:33 PM] Alex: wanna hang out?
[1/15/24, 10:35 PM] Jordan: maybe later
[1/15/24, 10:36 PM] Alex: cool, let me know
[1/15/24, 10:40 PM] Jordan: sure thing
[1/16/24, 9:15 AM] Alex: good morning!
[1/16/24, 9:20 AM] Jordan: morning! how are you?
[1/16/24, 9:22 AM] Alex: doing good, thanks for asking
[1/16/24, 9:25 AM] Jordan: that's great to hear"""
    
    # Analyze the chat
    analysis_result = analyze_chat(sample_chat, "Jordan")
    
    if not analysis_result["success"]:
        print("❌ Cannot proceed without successful analysis")
        return
    
    analysis_data = analysis_result["analysis"]
    session_id = None
    
    # Chat with the persona
    print("\n" + "=" * 50)
    print("Starting conversation...")
    
    # First message
    session_id = chat_with_persona(
        "Hey, I've been thinking about our last conversation...",
        analysis_data,
        session_id
    )
    
    # Second message
    session_id = chat_with_persona(
        "I wanted to tell you how I really felt about everything that happened.",
        analysis_data,
        session_id
    )
    
    # Third message
    session_id = chat_with_persona(
        "Do you think we could have handled things differently?",
        analysis_data,
        session_id
    )
    
    # Generate closure letter
    print("\n" + "=" * 50)
    closure_letter = generate_closure_letter(analysis_data, "Jordan")
    
    print("\n" + "=" * 50)
    print("✅ Example completed!")

if __name__ == "__main__":
    main()
