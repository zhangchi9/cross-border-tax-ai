"""
Session Service

Handles session management and state conversions between science team format
and frontend format.

Owner: Backend Engineering Team
"""
from typing import Dict, Any
from backend_eng.models.schemas import CaseFile, ChatMessage, UserProfile, ConversationPhase


def workflow_state_to_case_file(workflow_result: Dict[str, Any]) -> CaseFile:
    """
    Convert science team's workflow result to frontend case_file format

    Args:
        workflow_result: Result dictionary from science team's workflow

    Returns:
        CaseFile object for frontend consumption
    """
    state = workflow_result.get('state', {})

    # Convert workflow messages to frontend ChatMessage format
    messages = []
    for msg in state.get('messages', []):
        messages.append(ChatMessage(
            id=msg.get('id', ''),
            role=msg.get('role', ''),
            content=msg.get('content', ''),
            timestamp=msg.get('timestamp', '')
        ))

    # Map workflow phase to frontend conversation phase
    phase_mapping = {
        'intake': ConversationPhase.INTAKE,
        'forms_analysis': ConversationPhase.CLARIFICATIONS,
        'completed': ConversationPhase.FINAL_SUGGESTIONS
    }

    conversation_phase = phase_mapping.get(
        workflow_result.get('current_phase', 'intake'),
        ConversationPhase.INTAKE
    )

    # Build user profile
    user_profile_data = state.get('user_profile', {})
    user_profile = UserProfile(
        countries_involved=state.get('jurisdictions', []),
        tax_residency_status=user_profile_data.get('tax_residency_status'),
        visa_immigration_status=user_profile_data.get('visa_immigration_status'),
        filing_status=user_profile_data.get('filing_status'),
        tax_year=user_profile_data.get('tax_year'),
        sources_of_income=state.get('income_types', []),
        foreign_assets=user_profile_data.get('foreign_assets', []),
        credits_deductions=user_profile_data.get('credits_deductions', [])
    )

    case_file = CaseFile(
        session_id=workflow_result.get('session_id', ''),
        user_profile=user_profile,
        jurisdictions=state.get('jurisdictions', []),
        income_types=state.get('income_types', []),
        assigned_tags=workflow_result.get('assigned_tags', []),
        potential_issues=state.get('potential_issues', []),
        unanswered_questions=[],  # Could be derived from workflow state
        citations=[],  # Could be derived from workflow state
        conversation_phase=conversation_phase,
        messages=messages,
        created_at=state.get('created_at', ''),
        updated_at=state.get('updated_at', '')
    )

    return case_file