"""
Agentic Tax Consultant
Replaces tax_consultant.py with the new agentic framework
"""
import re
from typing import AsyncGenerator, Dict, Any, List, Tuple, Optional
from datetime import datetime

from .models import CaseFile, ConversationPhase, MessageRole
from agents import LLMCrossBorderTaxOrchestrator


class AgenticTaxConsultant:
    """
    Agentic tax consultant that uses the structured agent framework
    """

    def __init__(self):
        self.orchestrator = LLMCrossBorderTaxOrchestrator()
        self.active_sessions = {}  # Map case_file.session_id to agent session_id

    async def generate_response(self, case_file: CaseFile, user_message: str) -> AsyncGenerator[Tuple[str, List[str]], None]:
        """
        Generate response using the agentic framework
        """
        try:
            session_id = case_file.session_id

            # Check if we have an existing agent session
            if session_id not in self.active_sessions:
                # Start new agent session
                response = await self.orchestrator.start_consultation(user_message)
                self.active_sessions[session_id] = response["session_id"]
            else:
                # Continue existing session
                agent_session_id = self.active_sessions[session_id]
                response = await self.orchestrator.continue_consultation(agent_session_id, user_message)

            # Process agent response
            yield self._process_agent_response(response, case_file)

        except Exception as e:
            yield f"I apologize, but I encountered an error: {str(e)}", []

    def _process_agent_response(self, agent_response: Dict[str, Any], case_file: CaseFile) -> Tuple[str, List[str]]:
        """
        Process agent response and format for the API
        """
        message = agent_response.get("message", "")
        quick_replies = []

        # Check if we've transitioned to forms analysis
        if agent_response.get("transition") and agent_response.get("forms_analysis"):
            # Agent completed analysis - format comprehensive response
            forms_analysis = agent_response["forms_analysis"]
            message = self._format_comprehensive_analysis(forms_analysis)

            # Update case file phase
            case_file.conversation_phase = ConversationPhase.FINAL_SUGGESTIONS

            # No quick replies for final analysis
            quick_replies = []

        else:
            # Regular conversation - generate appropriate quick replies
            quick_replies = self._generate_quick_replies(agent_response, message)

        return message, quick_replies

    def _format_comprehensive_analysis(self, forms_analysis: Dict[str, Any]) -> str:
        """
        Format the forms analysis into a comprehensive response
        """
        sections = []

        # Analysis summary
        summary = forms_analysis.get("analysis_summary", "")
        if summary:
            sections.append(f"## Analysis Summary\n\n{summary}")

        # Required forms with priority indicators
        required_forms = forms_analysis.get("required_forms", [])
        if required_forms:
            sections.append("## Required Tax Forms")

            # Group by priority
            high_priority = [f for f in required_forms if f.get("priority") == "high"]
            medium_priority = [f for f in required_forms if f.get("priority") == "medium"]
            low_priority = [f for f in required_forms if f.get("priority") == "low"]

            for priority_group, forms, emoji in [
                ("High Priority", high_priority, "🔴"),
                ("Medium Priority", medium_priority, "🟡"),
                ("Lower Priority", low_priority, "🟢")
            ]:
                if forms:
                    sections.append(f"### {emoji} {priority_group}")
                    for form in forms:
                        sections.append(f"**{form['form']}** ({form['jurisdiction']})")
                        sections.append(f"- Due: {form['due_date']}")
                        if form.get('description'):
                            sections.append(f"- {form['description']}")
                        sections.append("")

        # Complexity assessment
        complexity = forms_analysis.get("estimated_complexity", "")
        if complexity:
            complexity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(complexity, "🟢")
            sections.append(f"## Complexity Assessment\n\n{complexity_emoji} **{complexity.title()} Complexity**")

        # Priority deadlines
        deadlines = forms_analysis.get("priority_deadlines", [])
        if deadlines:
            sections.append("## Upcoming Priority Deadlines")
            for deadline in deadlines:
                sections.append(f"- **{deadline['form']}** ({deadline['jurisdiction']}): {deadline['due_date']}")

        # Recommendations
        recommendations = forms_analysis.get("recommendations", [])
        if recommendations:
            sections.append("## Key Recommendations")
            for i, rec in enumerate(recommendations, 1):
                sections.append(f"{i}. {rec}")

        # Next steps
        next_steps = forms_analysis.get("next_steps", [])
        if next_steps:
            sections.append("## Immediate Next Steps")
            for i, step in enumerate(next_steps, 1):
                sections.append(f"{i}. {step}")

        # Compliance checklist
        checklist = forms_analysis.get("compliance_checklist", [])
        if checklist:
            sections.append("## Compliance Checklist")
            for item in checklist[:5]:  # Show first 5 items
                status_emoji = "⏳" if item.get("status") == "pending" else "✅"
                sections.append(f"{status_emoji} {item['task']} (Due: {item.get('due_date', 'TBD')})")

        return "\n\n".join(sections)

    def _generate_quick_replies(self, agent_response: Dict[str, Any], message: str) -> List[str]:
        """
        Generate appropriate quick replies based on the agent response
        """
        question_type = agent_response.get("question_type", "")

        # Default quick replies based on question type
        if "gating" in question_type:
            return ["Yes", "No", "Not sure"]

        # Check message content for specific patterns
        message_lower = message.lower()

        # Residency questions
        if any(word in message_lower for word in ["resident", "citizenship", "citizen"]):
            return ["US resident", "Canadian resident", "Neither", "Both"]

        # Employment questions
        if any(word in message_lower for word in ["work", "employment", "job", "income"]):
            return ["Yes", "No", "Partially"]

        # Property questions
        if any(word in message_lower for word in ["property", "real estate", "rental", "own"]):
            return ["Yes", "No", "Planning to"]

        # Account questions
        if any(word in message_lower for word in ["account", "investment", "bank"]):
            return ["Yes", "No", "Not sure"]

        # General yes/no for other questions
        if "?" in message:
            return ["Yes", "No"]

        return []

    def update_case_file(self, case_file: CaseFile, user_message: str, assistant_response: str) -> CaseFile:
        """
        Update case file with information extracted from conversation
        """
        # Extract basic information from user message
        self._extract_user_info(case_file, user_message)

        # Update assigned tags from agent session
        self._update_assigned_tags(case_file)

        # Update conversation phase
        self._update_conversation_phase(case_file)

        # Update timestamp
        case_file.updated_at = datetime.now()

        return case_file

    def _update_assigned_tags(self, case_file: CaseFile) -> None:
        """
        Update assigned tags from agent session
        """
        session_id = case_file.session_id
        if session_id in self.active_sessions:
            agent_session_id = self.active_sessions[session_id]
            summary = self.orchestrator.get_session_summary(agent_session_id)
            if summary and summary.get("assigned_tags"):
                # Update case file with tags from agent session
                case_file.assigned_tags = summary["assigned_tags"]

    def _extract_user_info(self, case_file: CaseFile, message: str) -> None:
        """
        Extract relevant information from user message and update case file
        """
        message_lower = message.lower()

        # Extract countries
        countries = self._extract_countries(message)
        for country in countries:
            if country not in case_file.user_profile.countries_involved:
                case_file.user_profile.countries_involved.append(country)
            if country not in case_file.jurisdictions:
                case_file.jurisdictions.append(country)

        # Extract tax year
        tax_year_match = re.search(r'\b(20\d{2})\b', message)
        if tax_year_match and not case_file.user_profile.tax_year:
            case_file.user_profile.tax_year = int(tax_year_match.group(1))

        # Extract income types
        income_keywords = {
            'salary': 'salary', 'wages': 'wages', 'employment': 'employment',
            'dividend': 'dividends', 'interest': 'interest', 'rental': 'rental income',
            'business': 'business income', 'freelance': 'freelance income',
            'pension': 'pension', 'retirement': 'retirement income',
            'social security': 'social security'
        }

        for keyword, income_type in income_keywords.items():
            if keyword in message_lower and income_type not in case_file.user_profile.sources_of_income:
                case_file.user_profile.sources_of_income.append(income_type)
                if income_type not in case_file.income_types:
                    case_file.income_types.append(income_type)

        # Extract assets
        asset_keywords = {
            'property': 'real estate', 'real estate': 'real estate', 'house': 'real estate',
            'stocks': 'stocks', 'bonds': 'bonds', 'investment': 'investments',
            'bank account': 'bank accounts', 'cryptocurrency': 'cryptocurrency',
            'business': 'business ownership'
        }

        for keyword, asset_type in asset_keywords.items():
            if keyword in message_lower and asset_type not in case_file.user_profile.foreign_assets:
                case_file.user_profile.foreign_assets.append(asset_type)

        # Extract residency status
        if 'us resident' in message_lower or 'american resident' in message_lower:
            case_file.user_profile.tax_residency_status = 'US resident'
        elif 'canadian resident' in message_lower:
            case_file.user_profile.tax_residency_status = 'Canadian resident'
        elif 'citizen' in message_lower and 'us' in message_lower:
            case_file.user_profile.tax_residency_status = 'US citizen'

    def _extract_countries(self, message: str) -> List[str]:
        """
        Extract country names from message
        """
        countries = []
        country_keywords = {
            'us': 'United States', 'usa': 'United States', 'united states': 'United States',
            'america': 'United States', 'american': 'United States',
            'canada': 'Canada', 'canadian': 'Canada',
            'uk': 'United Kingdom', 'britain': 'United Kingdom', 'england': 'United Kingdom',
            'germany': 'Germany', 'german': 'Germany',
            'france': 'France', 'french': 'France',
            'australia': 'Australia', 'australian': 'Australia',
            'japan': 'Japan', 'japanese': 'Japan',
            'china': 'China', 'chinese': 'China',
            'india': 'India', 'indian': 'India',
            'mexico': 'Mexico', 'mexican': 'Mexico'
        }

        message_lower = message.lower()
        for keyword, country in country_keywords.items():
            if keyword in message_lower and country not in countries:
                countries.append(country)

        return countries

    def _update_conversation_phase(self, case_file: CaseFile) -> None:
        """
        Update conversation phase based on information completeness
        """
        profile = case_file.user_profile

        # Check if basic intake info is complete
        has_countries = len(profile.countries_involved) >= 1  # At least one country
        has_income_or_assets = len(profile.sources_of_income) > 0 or len(profile.foreign_assets) > 0

        # Count messages to gauge conversation progress
        user_messages = [msg for msg in case_file.messages if msg.role == MessageRole.USER]

        if case_file.conversation_phase == ConversationPhase.INTAKE:
            if has_countries and has_income_or_assets and len(user_messages) >= 3:
                case_file.conversation_phase = ConversationPhase.CLARIFICATIONS
        elif case_file.conversation_phase == ConversationPhase.CLARIFICATIONS:
            if len(user_messages) >= 5:  # After sufficient clarifications
                # Phase will be updated to FINAL_SUGGESTIONS when agent completes analysis
                pass

    def can_provide_final_suggestions(self, case_file: CaseFile) -> bool:
        """
        Determine if we can provide final suggestions
        """
        # Check if agent session has completed analysis
        session_id = case_file.session_id
        if session_id in self.active_sessions:
            agent_session_id = self.active_sessions[session_id]
            summary = self.orchestrator.get_session_summary(agent_session_id)
            return summary and summary.get("forms_analysis_completed", False)

        # Fallback: check basic requirements
        profile = case_file.user_profile
        has_countries = len(profile.countries_involved) >= 1
        has_income_or_assets = len(profile.sources_of_income) > 0 or len(profile.foreign_assets) > 0
        sufficient_interaction = len(case_file.messages) >= 6

        return has_countries and has_income_or_assets and sufficient_interaction

    async def force_final_suggestions(self, case_file: CaseFile) -> AsyncGenerator[Tuple[str, List[str]], None]:
        """
        Force transition to final suggestions/forms analysis
        """
        try:
            session_id = case_file.session_id

            if session_id in self.active_sessions:
                agent_session_id = self.active_sessions[session_id]
                response = await self.orchestrator.force_forms_analysis(agent_session_id)
            else:
                yield "Please start a conversation first before requesting final suggestions.", []
                return

            # Process agent response
            yield self._process_agent_response(response, case_file)

        except Exception as e:
            yield f"I apologize, but I encountered an error generating final suggestions: {str(e)}", []

    def get_agent_session_summary(self, case_file: CaseFile) -> Optional[Dict[str, Any]]:
        """
        Get the agent session summary if available
        """
        session_id = case_file.session_id
        if session_id in self.active_sessions:
            agent_session_id = self.active_sessions[session_id]
            return self.orchestrator.get_session_summary(agent_session_id)
        return None