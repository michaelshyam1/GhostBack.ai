"""
Pydantic models for GhostBack.ai API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """Individual chat message"""
    text: str = Field(..., description="Message content")
    sender: str = Field(..., description="Sender name")
    timestamp: str = Field(..., description="Message timestamp")


class ChatAnalysisRequest(BaseModel):
    """Request to analyze chat history"""
    chat_text: str = Field(..., description="Raw chat export text")
    ghost_name: Optional[str] = Field(None, description="Name of person to analyze (optional)")


class ChatAnalysisResponse(BaseModel):
    """Response from chat analysis"""
    success: bool = Field(..., description="Whether analysis was successful")
    message: str = Field(..., description="Status message")
    participants: Optional[List[str]] = Field(None, description="Identified participants")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    error: Optional[str] = Field(None, description="Error message if failed")


class ChatRequest(BaseModel):
    """Request to chat with AI persona"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    analysis_data: Optional[Dict[str, Any]] = Field(None, description="Pre-computed analysis data")


class ChatResponse(BaseModel):
    """Response from AI chat"""
    success: bool = Field(..., description="Whether response was generated")
    message: str = Field(..., description="AI response message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    error: Optional[str] = Field(None, description="Error message if failed")


class ClosureLetterRequest(BaseModel):
    """Request to generate closure letter"""
    analysis_data: Dict[str, Any] = Field(..., description="Analysis data for the person")
    ghost_name: str = Field(..., description="Name of the person")


class ClosureLetterResponse(BaseModel):
    """Response with closure letter"""
    success: bool = Field(..., description="Whether letter was generated")
    letter: Optional[str] = Field(None, description="Generated closure letter")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")


class SafetyWarning(BaseModel):
    """Safety warning model"""
    type: str = Field(..., description="Type of warning")
    message: str = Field(..., description="Warning message")
    urgency: str = Field(..., description="Urgency level: low, medium, high, immediate")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional warning details")


class SafetyAnalysis(BaseModel):
    """Safety analysis response"""
    warning_level: str = Field(..., description="Overall warning level: none, low, medium, high, crisis")
    warnings: List[SafetyWarning] = Field(..., description="List of specific warnings")
    recommendation: str = Field(..., description="Personalized safety recommendation")
    should_pause: bool = Field(..., description="Whether conversation should be paused")
    crisis_resources: Optional[List[Dict[str, str]]] = Field(None, description="Crisis resources if needed")


class ChatWithSafetyRequest(BaseModel):
    """Enhanced chat request with safety monitoring"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    analysis_data: Optional[Dict[str, Any]] = Field(None, description="Pre-computed analysis data")
    enable_safety_monitoring: bool = Field(True, description="Enable safety monitoring")


class ChatWithSafetyResponse(BaseModel):
    """Enhanced chat response with safety analysis"""
    success: bool = Field(..., description="Whether response was generated")
    message: str = Field(..., description="AI response message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    safety_analysis: Optional[SafetyAnalysis] = Field(None, description="Safety analysis results")
    error: Optional[str] = Field(None, description="Error message if failed")


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
