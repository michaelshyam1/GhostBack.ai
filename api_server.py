"""
FastAPI server for GhostBack.ai
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
from typing import Dict, Any
import uuid

from api_models import (
    ChatAnalysisRequest, ChatAnalysisResponse,
    ChatRequest, ChatResponse,
    ChatWithSafetyRequest, ChatWithSafetyResponse,
    ClosureLetterRequest, ClosureLetterResponse,
    HealthResponse, ErrorResponse, SafetyAnalysis, SafetyWarning
)
from api_core import ChatAnalyzer, AIPersona
from safety_analyzer import EmotionalSafetyAnalyzer

# Initialize FastAPI app
app = FastAPI(
    title="GhostBack.ai API",
    description="API for AI-assisted emotional closure through chat analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
analyzer = ChatAnalyzer()
persona = AIPersona()
safety_analyzer = EmotionalSafetyAnalyzer()

# In-memory storage for sessions (use Redis/DB in production)
sessions: Dict[str, Dict[str, Any]] = {}


def get_openai_key():
    """Get OpenAI API key from environment or raise error."""
    key = os.getenv("OPENAI_API_KEY")
    if not key or key == "your_openai_api_key_here":
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
    return key


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health check."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )


@app.post("/analyze", response_model=ChatAnalysisResponse)
async def analyze_chat(request: ChatAnalysisRequest):
    """
    Analyze chat history and extract conversational patterns.
    
    This endpoint parses WhatsApp chat exports and analyzes the texting patterns
    of a specific person to create an AI persona profile.
    """
    try:
        # Parse the chat text
        messages = analyzer.parse_whatsapp_chat(request.chat_text)
        
        if len(messages) < 5:
            return ChatAnalysisResponse(
                success=False,
                message=f"Only found {len(messages)} messages. Need at least 5.",
                error="Insufficient messages for analysis"
            )
        
        # Identify participants
        person1, person2 = analyzer.identify_participants(messages)
        
        if not person1 or not person2:
            return ChatAnalysisResponse(
                success=False,
                message="Could not identify participants in chat.",
                error="Invalid chat format"
            )
        
        participants = [person1, person2]
        
        # If ghost_name is specified, analyze that person
        if request.ghost_name:
            if request.ghost_name not in participants:
                return ChatAnalysisResponse(
                    success=False,
                    message=f"Person '{request.ghost_name}' not found in chat participants.",
                    error="Person not found"
                )
            ghost_name = request.ghost_name
        else:
            # Use the most active participant
            ghost_name = person1
        
        # Analyze the chat
        analysis = analyzer.analyze_chat(messages, ghost_name)
        
        if "error" in analysis:
            return ChatAnalysisResponse(
                success=False,
                message=analysis["error"],
                error=analysis["error"]
            )
        
        return ChatAnalysisResponse(
            success=True,
            message=f"Successfully analyzed {len(messages)} messages for {ghost_name}",
            participants=participants,
            analysis=analysis
        )
        
    except Exception as e:
        return ChatAnalysisResponse(
            success=False,
            message=f"Analysis failed: {str(e)}",
            error=str(e)
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_with_persona(request: ChatRequest):
    """
    Chat with the AI persona based on previous analysis.
    
    This endpoint allows you to have a conversation with an AI that mimics
    the texting style of someone from your chat history.
    """
    try:
        # Validate OpenAI API key
        get_openai_key()
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            if not request.analysis_data:
                return ChatResponse(
                    success=False,
                    message="No analysis data provided and no existing session found.",
                    error="Missing analysis data"
                )
            sessions[session_id] = {
                "analysis": request.analysis_data,
                "chat_history": [],
                "session_start": datetime.now()
            }
        
        session = sessions[session_id]
        
        # Add user message to history
        session["chat_history"].append({
            "role": "user",
            "content": request.message
        })
        
        # Generate AI response
        ghost_name = session["analysis"].get("ghost_name", "Unknown")
        response_text = persona.generate_response(
            session["chat_history"],
            session["analysis"],
            ghost_name
        )
        
        # Add AI response to history
        session["chat_history"].append({
            "role": "assistant",
            "content": response_text
        })
        
        return ChatResponse(
            success=True,
            message=response_text,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ChatResponse(
            success=False,
            message=f"Chat failed: {str(e)}",
            error=str(e)
        )


@app.post("/chat/safe", response_model=ChatWithSafetyResponse)
async def chat_with_safety_monitoring(request: ChatWithSafetyRequest):
    """
    Chat with the AI persona with emotional safety monitoring.
    
    This endpoint provides the same chat functionality but includes background
    monitoring for emotional safety and provides warnings when needed.
    """
    try:
        # Validate OpenAI API key
        get_openai_key()
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            if not request.analysis_data:
                return ChatWithSafetyResponse(
                    success=False,
                    message="No analysis data provided and no existing session found.",
                    error="Missing analysis data"
                )
            sessions[session_id] = {
                "analysis": request.analysis_data,
                "chat_history": [],
                "session_start": datetime.now()
            }
        
        session = sessions[session_id]
        
        # Add user message to history
        session["chat_history"].append({
            "role": "user",
            "content": request.message
        })
        
        # Safety analysis
        safety_analysis = None
        if request.enable_safety_monitoring:
            safety_result = safety_analyzer.analyze_conversation_safety(
                session["chat_history"],
                session.get("session_start")
            )
            
            # Convert to Pydantic model
            warnings = []
            for warning in safety_result.get("warnings", []):
                warnings.append(SafetyWarning(
                    type=warning["type"],
                    message=warning["message"],
                    urgency=warning["urgency"],
                    details=warning.get("details")
                ))
            
            safety_analysis = SafetyAnalysis(
                warning_level=safety_result["warning_level"],
                warnings=warnings,
                recommendation=safety_analyzer.generate_safety_recommendation(safety_result),
                should_pause=safety_analyzer.should_pause_conversation(safety_result),
                crisis_resources=safety_analyzer.get_crisis_resources() if safety_result["warning_level"] == "crisis" else None
            )
            
            # If crisis detected, don't generate AI response
            if safety_result["warning_level"] == "crisis":
                return ChatWithSafetyResponse(
                    success=True,
                    message="I'm concerned about your safety. Please see the safety recommendations below.",
                    session_id=session_id,
                    safety_analysis=safety_analysis
                )
        
        # Generate AI response (unless paused for safety)
        if not safety_analysis or not safety_analysis.should_pause:
            ghost_name = session["analysis"].get("ghost_name", "Unknown")
            response_text = persona.generate_response(
                session["chat_history"],
                session["analysis"],
                ghost_name
            )
            
            # Add AI response to history
            session["chat_history"].append({
                "role": "assistant",
                "content": response_text
            })
        else:
            response_text = "I think it would be good to pause here and take care of yourself. Please see the safety recommendations below."
        
        return ChatWithSafetyResponse(
            success=True,
            message=response_text,
            session_id=session_id,
            safety_analysis=safety_analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ChatWithSafetyResponse(
            success=False,
            message=f"Chat failed: {str(e)}",
            error=str(e)
        )


@app.post("/closure-letter", response_model=ClosureLetterResponse)
async def generate_closure_letter(request: ClosureLetterRequest):
    """
    Generate a closure letter based on chat analysis.
    
    This endpoint creates a compassionate letter to help with emotional closure
    based on the analyzed communication patterns.
    """
    try:
        # Validate OpenAI API key
        get_openai_key()
        
        # Generate closure letter
        letter = persona.generate_closure_letter(
            request.analysis_data,
            request.ghost_name
        )
        
        if letter.startswith("❌"):
            return ClosureLetterResponse(
                success=False,
                error=letter
            )
        
        return ClosureLetterResponse(
            success=True,
            letter=letter
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ClosureLetterResponse(
            success=False,
            error=f"Failed to generate closure letter: {str(e)}"
        )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session data including chat history and analysis."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "analysis": sessions[session_id]["analysis"],
        "chat_history": sessions[session_id]["chat_history"],
        "session_start": sessions[session_id].get("session_start")
    }


@app.get("/session/{session_id}/safety")
async def get_session_safety_analysis(session_id: str):
    """Get safety analysis for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    safety_result = safety_analyzer.analyze_conversation_safety(
        session["chat_history"],
        session.get("session_start")
    )
    
    # Convert to Pydantic model
    warnings = []
    for warning in safety_result.get("warnings", []):
        warnings.append(SafetyWarning(
            type=warning["type"],
            message=warning["message"],
            urgency=warning["urgency"],
            details=warning.get("details")
        ))
    
    safety_analysis = SafetyAnalysis(
        warning_level=safety_result["warning_level"],
        warnings=warnings,
        recommendation=safety_analyzer.generate_safety_recommendation(safety_result),
        should_pause=safety_analyzer.should_pause_conversation(safety_result),
        crisis_resources=safety_analyzer.get_crisis_resources() if safety_result["warning_level"] == "crisis" else None
    )
    
    return {
        "session_id": session_id,
        "safety_analysis": safety_analysis,
        "session_duration_minutes": safety_result.get("session_duration_minutes", 0)
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its data."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    return {"message": "Session deleted successfully"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
