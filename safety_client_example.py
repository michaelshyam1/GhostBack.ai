#!/usr/bin/env python3
"""
Example client demonstrating safety monitoring features
"""

import requests
import json
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_safety_monitoring():
    """Test the safety monitoring features."""
    print("Testing GhostBack.ai Safety Monitoring")
    print("=" * 60)
    
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
    
    # 1. Analyze the chat
    print("Step 1: Analyzing chat history...")
    analysis_response = requests.post(f"{BASE_URL}/analyze", json={
        "chat_text": sample_chat,
        "ghost_name": "Jordan"
    })
    
    if not analysis_response.json()["success"]:
        print("Analysis failed")
        return
    
    analysis_data = analysis_response.json()["analysis"]
    print("Analysis complete")
    
    # 2. Start a conversation with safety monitoring
    print("\nStep 2: Starting conversation with safety monitoring...")
    
    # Simulate a normal conversation first
    print("\n--- Normal conversation ---")
    response = requests.post(f"{BASE_URL}/chat/safe", json={
        "message": "Hey Jordan, I've been thinking about our friendship lately.",
        "analysis_data": analysis_data,
        "enable_safety_monitoring": True
    })
    
    result = response.json()
    print(f"AI: {result['message']}")
    if result.get('safety_analysis'):
        print_safety_analysis(result['safety_analysis'])
    
    session_id = result['session_id']
    
    # Simulate escalating emotions
    print("\n--- Escalating emotions ---")
    escalating_messages = [
        "I just feel like I can't trust anyone anymore. Everyone always leaves me.",
        "I hate how things ended between us. I wish I could go back and change everything.",
        "I blame myself for everything that went wrong. I'm worthless and useless.",
        "I can't go on like this. I feel so alone and abandoned.",
        "I just want to end it all. There's no point in living anymore."
    ]
    
    for i, message in enumerate(escalating_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")
        
        response = requests.post(f"{BASE_URL}/chat/safe", json={
            "message": message,
            "session_id": session_id,
            "enable_safety_monitoring": True
        })
        
        result = response.json()
        print(f"AI: {result['message']}")
        
        if result.get('safety_analysis'):
            print_safety_analysis(result['safety_analysis'])
            
            # If crisis detected, show resources and stop
            if result['safety_analysis']['warning_level'] == 'crisis':
                print("\nCRISIS DETECTED - Conversation paused for safety")
                break
        
        # Small delay to simulate real conversation
        time.sleep(1)
    
    # 3. Check session safety analysis
    print("\nStep 3: Checking overall session safety...")
    safety_response = requests.get(f"{BASE_URL}/session/{session_id}/safety")
    safety_data = safety_response.json()
    
    print(f"Session Duration: {safety_data['session_duration_minutes']:.1f} minutes")
    print_safety_analysis(safety_data['safety_analysis'])
    
    print("\nSafety monitoring test completed!")

def print_safety_analysis(safety_analysis: Dict[str, Any]):
    """Print safety analysis in a readable format."""
    if not safety_analysis:
        return
    
    warning_level = safety_analysis['warning_level']
    warnings = safety_analysis.get('warnings', [])
    recommendation = safety_analysis.get('recommendation', '')
    should_pause = safety_analysis.get('should_pause', False)
    
    # Color coding for warning levels
    level_colors = {
        'none': '[GREEN]',
        'low': '[YELLOW]',
        'medium': '[ORANGE]',
        'high': '[RED]',
        'crisis': '[CRISIS]'
    }
    
    print(f"\n{level_colors.get(warning_level, '[NONE]')} Safety Level: {warning_level.upper()}")
    
    if warnings:
        print("Warnings:")
        for warning in warnings:
            urgency_icon = {
                'low': '[YELLOW]',
                'medium': '[ORANGE]', 
                'high': '[RED]',
                'immediate': '[CRISIS]'
            }.get(warning['urgency'], '[NONE]')
            
            print(f"   {urgency_icon} {warning['message']}")
    
    if recommendation:
        print(f"\nRecommendation:\n{recommendation}")
    
    if should_pause:
        print("\nConversation should be paused for safety")
    
    if safety_analysis.get('crisis_resources'):
        print("\nCrisis Resources:")
        for resource in safety_analysis['crisis_resources']:
            print(f"   - {resource['name']}: {resource['number']} - {resource['description']}")

def test_individual_message_analysis():
    """Test individual message safety analysis."""
    print("\nTesting Individual Message Analysis")
    print("=" * 40)
    
    test_messages = [
        "Hey, how are you?",
        "I'm feeling really sad today.",
        "I can't stop thinking about what happened.",
        "I hate myself for everything I did wrong.",
        "I want to kill myself.",
        "I just want to end it all."
    ]
    
    for message in test_messages:
        print(f"\nMessage: '{message}'")
        
        # This would normally be done by the safety analyzer
        # For demo purposes, we'll simulate the analysis
        response = requests.post(f"{BASE_URL}/chat/safe", json={
            "message": message,
            "analysis_data": {"ghost_name": "Test"},
            "enable_safety_monitoring": True
        })
        
        result = response.json()
        if result.get('safety_analysis'):
            print_safety_analysis(result['safety_analysis'])

if __name__ == "__main__":
    print("GhostBack.ai Safety Monitoring Demo")
    print("Make sure the API server is running: python run_api.py")
    print()
    
    try:
        # Test health first
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("API server is not running. Please start it with: python run_api.py")
            exit(1)
        
        test_safety_monitoring()
        test_individual_message_analysis()
        
    except requests.exceptions.ConnectionError:
        print("Cannot connect to API server. Please start it with: python run_api.py")
    except Exception as e:
        print(f"Error: {e}")
