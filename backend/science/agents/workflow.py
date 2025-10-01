"""
LangGraph Workflow for Tax Consultation

Owner: Science Team

This module defines the LangGraph workflow for tax consultation,
orchestrating the flow between IntakeNode, FormsAnalysisNode, and CompletionNode.
"""
import uuid
import asyncio
from typing import Dict, Any, List, Literal, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from science.config import science_config
from .state import TaxConsultationState, create_initial_state, add_message_to_state
from .nodes import IntakeNode, FormsAnalysisNode, CompletionNode


def should_continue_intake(state: TaxConsultationState) -> Literal["intake", "forms_analysis"]:
    """Conditional routing from intake phase"""
    # Check if we should transition based on explicit transition flag
    if state.get("should_transition", False):
        return "forms_analysis"

    # Auto-transition if we have enough tags (configured threshold)
    # AND sufficient conversation to have gathered context
    conversation_length = len(state.get("messages", []))
    if len(state.get("assigned_tags", [])) >= science_config.MIN_TAGS_FOR_TRANSITION:
        if conversation_length >= science_config.MIN_CONVERSATION_LENGTH:
            return "forms_analysis"

    # Check conversation length to prevent infinite loops
    # But allow for longer conversations since we have many questions (18 gating + module questions)
    # Maximum possible conversation: 18 gating + ~45 module questions = ~63 questions
    # Each question = 2 messages (assistant + user), so ~126 messages max
    # We'll set a generous limit
    if conversation_length >= 150:
        # Force transition after very long conversation
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

    async def start_consultation(self, initial_message: str = "", session_id: Optional[str] = None) -> Dict[str, Any]:
        """Start a new consultation session

        Args:
            initial_message: Initial message from user
            session_id: Optional session ID (auto-generated if not provided)

        Returns:
            Dict with session info and assistant response
        """

        if session_id is None:
            session_id = str(uuid.uuid4())

        initial_state = create_initial_state(session_id, initial_message)

        # Create thread config with recursion limit
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": science_config.WORKFLOW_RECURSION_LIMIT
        }

        # Run the workflow
        result = await self.app.ainvoke(initial_state, config)

        # Return with backward compatibility keys
        assistant_response = result.get("assistant_response", "")
        return {
            "session_id": session_id,
            "message": assistant_response,  # Legacy key
            "assistant_response": assistant_response,  # New key for consistency
            "quick_replies": result.get("quick_replies", []),
            "current_phase": result.get("current_phase", "intake"),
            "assigned_tags": result.get("assigned_tags", []),
            **result  # Include all state fields for backward compatibility
        }

    async def continue_consultation(self, session_id: str, message: str) -> Dict[str, Any]:
        """Continue an existing consultation session

        Args:
            session_id: Session ID from start_consultation
            message: User's message/response

        Returns:
            Dict with assistant response and updated state
        """

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

        # Return with backward compatibility keys
        assistant_response = result.get("assistant_response", "")
        return {
            "session_id": session_id,
            "message": assistant_response,  # Legacy key
            "assistant_response": assistant_response,  # New key for consistency
            "quick_replies": result.get("quick_replies", []),
            "current_phase": result.get("current_phase", "intake"),
            "assigned_tags": result.get("assigned_tags", []),
            "transition": result.get("should_transition", False),
            "forms_analysis": self._extract_forms_analysis(result) if result.get("current_phase") == "completed" else None,
            **result  # Include all state fields for backward compatibility
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

    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full session state

        Args:
            session_id: Session ID

        Returns:
            Full state dict or None if session not found
        """

        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 10
        }

        current_state = await self.app.aget_state(config)

        if not current_state:
            return None

        return current_state.values

    async def force_transition_to_forms_analysis(self, session_id: str) -> Dict[str, Any]:
        """Force transition to forms analysis (alias for force_forms_analysis)

        Args:
            session_id: Session ID

        Returns:
            Dict with forms analysis results
        """
        return await self.force_forms_analysis(session_id)

    # ============================================================================
    # SYNCHRONOUS WRAPPER METHODS (for testing and non-async contexts)
    # ============================================================================

    def start_consultation_sync(self, initial_message: str = "", session_id: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous wrapper for start_consultation

        Args:
            initial_message: Initial message from user
            session_id: Optional session ID (auto-generated if not provided)

        Returns:
            Dict with session info and assistant response
        """
        return asyncio.run(self.start_consultation(initial_message, session_id))

    def continue_consultation_sync(self, session_id: str, message: str) -> Dict[str, Any]:
        """Synchronous wrapper for continue_consultation

        Args:
            session_id: Session ID from start_consultation
            message: User's message/response

        Returns:
            Dict with assistant response and updated state
        """
        return asyncio.run(self.continue_consultation(session_id, message))

    def force_forms_analysis_sync(self, session_id: str) -> Dict[str, Any]:
        """Synchronous wrapper for force_forms_analysis

        Args:
            session_id: Session ID

        Returns:
            Dict with forms analysis results
        """
        return asyncio.run(self.force_forms_analysis(session_id))

    def force_transition_to_forms_analysis_sync(self, session_id: str) -> Dict[str, Any]:
        """Synchronous wrapper for force_transition_to_forms_analysis

        Args:
            session_id: Session ID

        Returns:
            Dict with forms analysis results
        """
        return asyncio.run(self.force_transition_to_forms_analysis(session_id))

    def get_session_summary_sync(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for get_session_summary

        Args:
            session_id: Session ID

        Returns:
            Session summary dict or None
        """
        return asyncio.run(self.get_session_summary(session_id))

    def get_session_state_sync(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for get_session_state

        Args:
            session_id: Session ID

        Returns:
            Full state dict or None
        """
        return asyncio.run(self.get_session_state(session_id))

    def get_conversation_history_sync(self, session_id: str) -> List[Dict[str, Any]]:
        """Synchronous wrapper for get_conversation_history

        Args:
            session_id: Session ID

        Returns:
            List of message dicts
        """
        return asyncio.run(self.get_conversation_history(session_id))

    def debug_session_sync(self, session_id: str) -> Dict[str, Any]:
        """Synchronous wrapper for debug_session

        Args:
            session_id: Session ID

        Returns:
            Debug info dict
        """
        return asyncio.run(self.debug_session(session_id))