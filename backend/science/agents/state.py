"""
LangGraph State Schema for Tax Consultation Workflow

Owner: Science Team
"""
from typing import Dict, List, Optional, Any, Literal
from typing_extensions import TypedDict
from datetime import datetime
import json


class Message(TypedDict):
    """Individual message in conversation"""
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str


class UserProfile(TypedDict):
    """User profile information"""
    countries_involved: List[str]
    tax_residency_status: Optional[str]
    visa_immigration_status: Optional[str]
    filing_status: Optional[str]
    tax_year: Optional[int]
    sources_of_income: List[str]
    foreign_assets: List[str]
    credits_deductions: List[str]


class TaxConsultationState(TypedDict):
    """
    Comprehensive state for the tax consultation workflow
    """

    # Session Management
    session_id: str

    # Conversation Flow
    messages: List[Message]
    current_message: str
    assistant_response: str
    quick_replies: List[str]

    # Workflow State
    current_phase: Literal["intake", "clarifications", "forms_analysis", "completed"]
    current_module: Optional[str]
    completed_modules: List[str]

    # Tax Information
    assigned_tags: List[str]
    user_profile: UserProfile
    jurisdictions: List[str]
    income_types: List[str]
    potential_issues: List[str]

    # Knowledge Base Context
    available_gating_questions: List[Dict[str, Any]]
    current_module_questions: List[Dict[str, Any]]
    knowledge_base: Dict[str, Any]

    # Forms Analysis Results
    required_forms: List[Dict[str, Any]]
    compliance_checklist: List[Dict[str, Any]]
    estimated_complexity: Optional[str]
    recommendations: List[str]
    next_steps: List[str]
    priority_deadlines: List[Dict[str, Any]]

    # Workflow Control
    should_transition: bool
    transition_reason: Optional[str]
    error_message: Optional[str]

    # Metadata
    created_at: str
    updated_at: str


def create_initial_state(session_id: str, initial_message: str = "") -> TaxConsultationState:
    """Create initial state for a new consultation session"""

    now = datetime.now().isoformat()

    return TaxConsultationState(
        # Session Management
        session_id=session_id,

        # Conversation Flow
        messages=[],
        current_message=initial_message,
        assistant_response="",
        quick_replies=[],

        # Workflow State
        current_phase="intake",
        current_module=None,
        completed_modules=[],

        # Tax Information
        assigned_tags=[],
        user_profile=UserProfile(
            countries_involved=[],
            tax_residency_status=None,
            visa_immigration_status=None,
            filing_status=None,
            tax_year=None,
            sources_of_income=[],
            foreign_assets=[],
            credits_deductions=[]
        ),
        jurisdictions=[],
        income_types=[],
        potential_issues=[],

        # Knowledge Base Context
        available_gating_questions=[],
        current_module_questions=[],
        knowledge_base={},

        # Forms Analysis Results
        required_forms=[],
        compliance_checklist=[],
        estimated_complexity=None,
        recommendations=[],
        next_steps=[],
        priority_deadlines=[],

        # Workflow Control
        should_transition=False,
        transition_reason=None,
        error_message=None,

        # Metadata
        created_at=now,
        updated_at=now
    )


def update_state_timestamp(state: TaxConsultationState) -> TaxConsultationState:
    """Update the state timestamp"""
    state["updated_at"] = datetime.now().isoformat()
    return state


def add_message_to_state(
    state: TaxConsultationState,
    role: Literal["user", "assistant", "system"],
    content: str
) -> TaxConsultationState:
    """Add a message to the conversation history"""

    import uuid

    message = Message(
        id=str(uuid.uuid4()),
        role=role,
        content=content,
        timestamp=datetime.now().isoformat()
    )

    state["messages"].append(message)
    state = update_state_timestamp(state)

    return state


def get_conversation_context(state: TaxConsultationState, last_n: int = 10) -> str:
    """Get formatted conversation context for LLM"""

    recent_messages = state["messages"][-last_n:]
    context_lines = []

    for msg in recent_messages:
        speaker = msg["role"].title()
        context_lines.append(f"{speaker}: {msg['content']}")

    return "\n".join(context_lines)


def serialize_state_for_storage(state: TaxConsultationState) -> str:
    """Serialize state for storage/transmission"""
    return json.dumps(state, default=str, indent=2)


def deserialize_state_from_storage(state_json: str) -> TaxConsultationState:
    """Deserialize state from storage"""
    return json.loads(state_json)