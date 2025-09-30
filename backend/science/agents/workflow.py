"""
LangGraph Workflow for Tax Consultation

Owner: Science Team

This module defines the LangGraph workflow for tax consultation,
orchestrating the flow between IntakeNode, FormsAnalysisNode, and CompletionNode.
"""
import uuid
from typing import Dict, Any, List, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from science.config import science_config
from .state import TaxConsultationState, create_initial_state, add_message_to_state
from .nodes import IntakeNode, FormsAnalysisNode, CompletionNode


def should_continue_intake(state: TaxConsultationState) -> Literal["intake", "forms_analysis"]:
    """Conditional routing from intake phase"""
    # Check if we should transition based on having enough tags or explicit transition flag
    if state.get("should_transition", False):
        return "forms_analysis"

    # Auto-transition if we have enough tags (configured threshold)
    if len(state.get("assigned_tags", [])) >= science_config.MIN_TAGS_FOR_TRANSITION:
        return "forms_analysis"

    # Check conversation length to prevent infinite loops
    conversation_length = len(state.get("messages", []))

    # For very short conversations (first few exchanges), always stay in intake
    if conversation_length <= 4:
        return "intake"

    # For longer conversations without sufficient tags, stay in intake a bit more
    if conversation_length <= 8:
        return "intake"

    # Force transition only after many messages to prevent infinite loops
    if conversation_length >= 10:
        return "forms_analysis"

    # Default to continuing intake
    return "intake"


def should_continue_forms_analysis(state: TaxConsultationState) -> Literal["completed", "intake"]:
    """Conditional routing from forms analysis phase"""
    # Always complete the forms analysis - don't loop back to intake
    return "completed"


def should_continue_completion(state: TaxConsultationState) -> Literal["completed", END]:
    """Conditional routing from completion phase"""
    # Always end when we reach completion to avoid loops
    return END


class TaxConsultationWorkflow:
    """
    LangGraph-based workflow for cross-border tax consultation

    This is the core AI workflow that science team owns and maintains.
    """

    def __init__(self):
        self.workflow = self._build_workflow()
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        # Create workflow
        workflow = StateGraph(TaxConsultationState)

        # Add nodes
        workflow.add_node("intake", IntakeNode())
        workflow.add_node("forms_analysis", FormsAnalysisNode())
        workflow.add_node("completed", CompletionNode())

        # Set entry point
        workflow.set_entry_point("intake")

        # Add conditional edges
        workflow.add_conditional_edges(
            "intake",
            should_continue_intake,
            {
                "intake": END,  # End after single intake response
                "forms_analysis": "forms_analysis"
            }
        )

        workflow.add_conditional_edges(
            "forms_analysis",
            should_continue_forms_analysis,
            {
                "completed": "completed",
                "intake": "intake"  # Fallback if needed
            }
        )

        workflow.add_conditional_edges(
            "completed",
            should_continue_completion,
            {
                "completed": "completed",
                END: END
            }
        )

        return workflow

    async def start_consultation(self, initial_message: str = "") -> Dict[str, Any]:
        """Start a new consultation session"""

        session_id = str(uuid.uuid4())
        initial_state = create_initial_state(session_id, initial_message)

        # Create thread config with recursion limit
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": science_config.WORKFLOW_RECURSION_LIMIT
        }

        # Run the workflow
        result = await self.app.ainvoke(initial_state, config)

        return {
            "session_id": session_id,
            "message": result.get("assistant_response", ""),
            "quick_replies": result.get("quick_replies", []),
            "current_phase": result.get("current_phase", "intake"),
            "assigned_tags": result.get("assigned_tags", []),
            "state": result
        }

    async def continue_consultation(self, session_id: str, message: str) -> Dict[str, Any]:
        """Continue an existing consultation session"""

        # Create thread config with recursion limit
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": science_config.WORKFLOW_RECURSION_LIMIT
        }

        # Get current state
        current_state = await self.app.aget_state(config)

        if not current_state:
            return {
                "error": "Session not found",
                "session_id": session_id
            }

        # Update state with new message
        state = current_state.values
        state["current_message"] = message

        # Run the workflow
        result = await self.app.ainvoke(state, config)

        return {
            "session_id": session_id,
            "message": result.get("assistant_response", ""),
            "quick_replies": result.get("quick_replies", []),
            "current_phase": result.get("current_phase", "intake"),
            "assigned_tags": result.get("assigned_tags", []),
            "transition": result.get("should_transition", False),
            "forms_analysis": self._extract_forms_analysis(result) if result.get("current_phase") == "completed" else None,
            "state": result
        }

    async def force_forms_analysis(self, session_id: str) -> Dict[str, Any]:
        """Force transition to forms analysis"""

        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 10  # Prevent infinite loops
        }

        # Get current state
        current_state = await self.app.aget_state(config)

        if not current_state:
            return {"error": "Session not found"}

        state = current_state.values

        # Check if we have enough information
        if len(state.get("assigned_tags", [])) < 1:
            return {
                "error": "No tags assigned yet. Please continue the conversation to gather more information.",
                "session_id": session_id
            }

        # Force transition
        state["should_transition"] = True
        state["transition_reason"] = "Forced transition to forms analysis"
        state["current_phase"] = "forms_analysis"
        state["current_message"] = "Please provide a summary of my tax requirements based on our conversation."

        # Run the workflow
        result = await self.app.ainvoke(state, config)

        return {
            "session_id": session_id,
            "message": result.get("assistant_response", ""),
            "current_phase": result.get("current_phase", "completed"),
            "transition": True,
            "forms_analysis": self._extract_forms_analysis(result),
            "state": result
        }

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary"""

        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 10  # Prevent infinite loops
        }

        # Get current state
        current_state = await self.app.aget_state(config)

        if not current_state:
            return None

        state = current_state.values

        return {
            "session_id": session_id,
            "current_phase": state.get("current_phase", "intake"),
            "assigned_tags": state.get("assigned_tags", []),
            "completed_modules": state.get("completed_modules", []),
            "current_module": state.get("current_module"),
            "message_count": len(state.get("messages", [])),
            "forms_analysis_completed": state.get("current_phase") == "completed",
            "has_sufficient_tags": len(state.get("assigned_tags", [])) >= science_config.MIN_TAGS_FOR_TRANSITION,
            "conversation_length": len(state.get("messages", []))
        }

    def _extract_forms_analysis(self, state: TaxConsultationState) -> Dict[str, Any]:
        """Extract forms analysis results from state"""

        return {
            "analysis_summary": f"Analysis completed for tags: {', '.join(state.get('assigned_tags', []))}",
            "required_forms": state.get("required_forms", []),
            "estimated_complexity": state.get("estimated_complexity", "medium"),
            "recommendations": state.get("recommendations", []),
            "next_steps": state.get("next_steps", []),
            "priority_deadlines": state.get("priority_deadlines", []),
            "compliance_checklist": state.get("compliance_checklist", [])
        }

    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""

        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 10  # Prevent infinite loops
        }

        # Get current state
        current_state = await self.app.aget_state(config)

        if not current_state:
            return []

        state = current_state.values
        return state.get("messages", [])

    async def debug_session(self, session_id: str) -> Dict[str, Any]:
        """Get detailed debug information for a session"""

        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 10  # Prevent infinite loops
        }

        # Get current state
        current_state = await self.app.aget_state(config)

        if not current_state:
            return {"error": "Session not found"}

        state = current_state.values

        return {
            "session_id": session_id,
            "current_phase": state.get("current_phase"),
            "current_module": state.get("current_module"),
            "completed_modules": state.get("completed_modules", []),
            "assigned_tags": state.get("assigned_tags", []),
            "message_count": len(state.get("messages", [])),
            "should_transition": state.get("should_transition", False),
            "transition_reason": state.get("transition_reason"),
            "error_message": state.get("error_message"),
            "user_profile": state.get("user_profile", {}),
            "jurisdictions": state.get("jurisdictions", []),
            "workflow_state": current_state.next,
            "created_at": state.get("created_at"),
            "updated_at": state.get("updated_at")
        }