"""
LLM-based Agent Orchestrator
Coordinates communication between LLM-powered intake and forms analysis agents
"""
import uuid
import asyncio
from typing import Dict, Any, Optional
from .base_agent import AgentOrchestrator
from .llm_intake_agent import LLMIntakeAgent
from .llm_forms_analysis_agent import LLMFormsAnalysisAgent


class LLMCrossBorderTaxOrchestrator(AgentOrchestrator):
    """LLM-powered orchestrator specifically for cross-border tax consultation"""

    def __init__(self):
        super().__init__()

        # Initialize and register LLM agents
        self.intake_agent = LLMIntakeAgent()
        self.forms_agent = LLMFormsAnalysisAgent()

        self.register_agent(self.intake_agent)
        self.register_agent(self.forms_agent)

    async def start_consultation(self, initial_message: str = "") -> Dict[str, Any]:
        """Start a new tax consultation session"""
        session_id = str(uuid.uuid4())

        if not initial_message:
            initial_message = "I need help with my cross-border tax situation."

        # Route to intake agent
        response = await self.route_to_agent_async(
            "llm_intake_agent",
            session_id,
            {"message": initial_message}
        )

        # Add session info to response
        response["session_id"] = session_id
        response["current_agent"] = "llm_intake_agent"

        return response

    async def continue_consultation(self, session_id: str, client_message: str) -> Dict[str, Any]:
        """Continue an existing consultation session"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found", "session_id": session_id}

        current_agent = session.context.get("current_agent", "llm_intake_agent")

        # Route message to current agent
        if current_agent == "llm_intake_agent":
            response = await self.route_to_agent_async(
                "llm_intake_agent",
                session_id,
                {"message": client_message}
            )

            # Check if intake agent wants to transition to forms analysis
            if response.get("transition", False):
                # Hand off to forms analysis agent
                forms_response = await self.route_to_agent_async(
                    "llm_forms_analysis_agent",
                    session_id,
                    response.get("handoff_data", {})
                )

                # Update session to reflect transition
                session.update_context("current_agent", "llm_forms_analysis_agent")
                session.update_context("forms_analysis_completed", True)

                # Return forms analysis results
                forms_response["session_id"] = session_id
                forms_response["current_agent"] = "llm_forms_analysis_agent"
                forms_response["transition"] = True
                forms_response["forms_analysis"] = forms_response

                return forms_response

        elif current_agent == "llm_forms_analysis_agent":
            # Forms analysis is typically final, but handle follow-up questions
            response = {
                "message": "Your forms analysis has been completed. If you have specific follow-up questions about the recommendations, please ask and I'll help clarify.",
                "session_id": session_id,
                "current_agent": "llm_forms_analysis_agent"
            }

        response["session_id"] = session_id
        response["current_agent"] = current_agent

        return response

    async def route_to_agent_async(self, agent_name: str, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route input to specified agent asynchronously"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        # Add session context to input
        input_data["session_context"] = session.context

        if agent_name == "llm_intake_agent":
            result = await self.intake_agent.process(input_data)
        elif agent_name == "llm_forms_analysis_agent":
            result = await self.forms_agent.process(input_data)
        else:
            return {"error": f"Unknown agent: {agent_name}"}

        # Update session with result context
        if "session_context" in result:
            session.context.update(result["session_context"])

        # Store any additional session metadata
        if "assigned_tags" in result:
            session.update_context("assigned_tags", result["assigned_tags"])

        if "current_agent" in result:
            session.update_context("current_agent", agent_name)

        # Add to session history
        session.add_to_history(agent_name, input_data, result)

        return result

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive session summary"""
        session = self.get_session(session_id)
        if not session:
            return None

        # Get summary from current agent
        current_agent = session.context.get("current_agent", "llm_intake_agent")
        agent_summary = {}

        if current_agent == "llm_intake_agent":
            agent_summary = self.intake_agent.get_session_summary()
        elif current_agent == "llm_forms_analysis_agent":
            # Forms analysis agent doesn't have session state, but we can provide metadata
            agent_summary = {
                "analysis_completed": True,
                "agent_type": "forms_analysis"
            }

        # Combine with session data
        summary = {
            "session_id": session_id,
            "current_agent": current_agent,
            "assigned_tags": session.context.get("assigned_tags", []),
            "forms_analysis_completed": session.context.get("forms_analysis_completed", False),
            **agent_summary
        }

        return summary

    async def force_forms_analysis(self, session_id: str) -> Dict[str, Any]:
        """Force transition to forms analysis even if intake isn't technically complete"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        # Get current state from intake agent
        intake_summary = self.intake_agent.get_session_summary()
        assigned_tags = intake_summary.get("assigned_tags", [])

        if not assigned_tags:
            return {
                "error": "No tags assigned yet. Please continue the conversation to gather more information.",
                "session_id": session_id
            }

        # Create handoff data
        handoff_data = {
            "tags": assigned_tags,
            "client_profile": session.context.get("conversation_state", {}).get("client_profile", {}),
            "case_summary": f"Forced analysis for tags: {', '.join(assigned_tags)}"
        }

        # Route to forms analysis
        forms_response = await self.route_to_agent_async(
            "llm_forms_analysis_agent",
            session_id,
            {"handoff_data": handoff_data}
        )

        # Update session
        session.update_context("current_agent", "llm_forms_analysis_agent")
        session.update_context("forms_analysis_completed", True)

        forms_response["session_id"] = session_id
        forms_response["current_agent"] = "llm_forms_analysis_agent"
        forms_response["transition"] = True
        forms_response["forms_analysis"] = forms_response

        return forms_response