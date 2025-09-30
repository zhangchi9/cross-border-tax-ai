"""
API Schemas

Pydantic models for request/response validation.

Owner: Backend Engineering Team
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class ConversationPhase(str, Enum):
    """Conversation phase enum"""
    INTAKE = "intake"
    CLARIFICATIONS = "clarifications"
    FINAL_SUGGESTIONS = "final_suggestions"


class MessageRole(str, Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual chat message"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    """User profile information collected during intake"""
    countries_involved: List[str] = Field(default_factory=list)
    tax_residency_status: Optional[str] = None
    visa_immigration_status: Optional[str] = None
    filing_status: Optional[str] = None
    tax_year: Optional[int] = None
    sources_of_income: List[str] = Field(default_factory=list)
    foreign_assets: List[str] = Field(default_factory=list)
    credits_deductions: List[str] = Field(default_factory=list)


class CaseFile(BaseModel):
    """Complete case file with all consultation data"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    session_id: str
    user_profile: UserProfile = Field(default_factory=UserProfile)
    jurisdictions: List[str] = Field(default_factory=list)
    income_types: List[str] = Field(default_factory=list)
    assigned_tags: List[str] = Field(default_factory=list)
    potential_issues: List[str] = Field(default_factory=list)
    unanswered_questions: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    conversation_phase: ConversationPhase = ConversationPhase.INTAKE
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    session_id: str
    message: str


class EditMessageRequest(BaseModel):
    """Request schema for editing a message"""
    session_id: str
    message_id: str
    new_content: str


class StreamingResponse(BaseModel):
    """Streaming response chunk schema"""
    content: str
    is_final: bool = False
    case_file: Optional[CaseFile] = None
    quick_replies: Optional[List[str]] = None


class FinalSuggestions(BaseModel):
    """Final suggestions schema"""
    key_issues: List[str]
    suggested_actions: List[str]
    documents_to_gather: List[str]
    likely_forms: List[str]
    risks_and_questions: List[str]
    citations: List[str]