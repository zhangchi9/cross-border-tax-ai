import google.generativeai as genai
from typing import AsyncGenerator, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import re

from .models import CaseFile, ConversationPhase, FinalSuggestions
from .config import settings


class TaxConsultant:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        return """
You are a cross-border tax consultant AI assistant. Your role is to help users navigate cross-border tax situations through these phases:

1. INTAKE & SCOPE: Collect basic information about:
   - Countries/jurisdictions involved
   - Tax residency status
   - Visa/immigration status if relevant
   - Filing status
   - Tax year
   - Sources of income
   - Foreign assets
   - Credits/deductions

2. CLARIFICATIONS: Ask targeted follow-up questions based on the information gathered.
   You MUST ask at least one round of clarifying questions before providing final suggestions.

3. FINAL SUGGESTIONS: Only after clarifications, provide:
   - Key issues identified
   - Suggested actions
   - Documents to gather
   - Filing forms likely involved (clearly marked as "likely")
   - Risks & open questions
   - Links to official resources

CRITICAL SAFETY RULES:
- Never collect highly sensitive identifiers (SSN, SIN, etc.)
- If user attempts to share sensitive info, warn and ask them not to
- Always mention jurisdiction variability and date sensitivity
- Include placeholders for government source links
- Handle common cross-border pairs (US↔Canada, US↔EU, etc.)
- Detect tax treaty relevance (residency tie-breakers, foreign tax credits, PFIC, etc.)

Respond conversationally but professionally. Ask one question at a time when possible.
"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response(self, case_file: CaseFile, user_message: str) -> AsyncGenerator[str, None]:
        conversation_history = self._build_conversation_context(case_file)

        prompt = f"""
{self.system_prompt}

CURRENT CASE CONTEXT:
{json.dumps(case_file.dict(), indent=2, default=str)}

CONVERSATION HISTORY:
{conversation_history}

USER MESSAGE: {user_message}

Based on the current phase ({case_file.conversation_phase}) and information gathered, provide an appropriate response.
If this is the intake phase and basic info is still missing, focus on gathering that.
If basic info is complete but you haven't asked clarifying questions, move to clarifications phase.
Only provide final suggestions after asking clarifying questions.
"""

        try:
            response = await self.model.generate_content_async(prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"I apologize, but I encountered an error. Please try again. Error: {str(e)}"

    def _build_conversation_context(self, case_file: CaseFile) -> str:
        context = []
        for msg in case_file.messages[-10:]:  # Last 10 messages for context
            context.append(f"{msg.role.upper()}: {msg.content}")
        return "\n".join(context)

    def update_case_file(self, case_file: CaseFile, user_message: str, assistant_response: str) -> CaseFile:
        # Extract information from user message and update case file
        self._extract_user_info(case_file, user_message)

        # Update conversation phase based on information completeness
        self._update_conversation_phase(case_file)

        return case_file

    def _extract_user_info(self, case_file: CaseFile, message: str) -> None:
        message_lower = message.lower()

        # Extract countries
        countries = self._extract_countries(message)
        if countries:
            case_file.user_profile.countries_involved.extend([c for c in countries if c not in case_file.user_profile.countries_involved])
            case_file.jurisdictions.extend([c for c in countries if c not in case_file.jurisdictions])

        # Extract tax year
        tax_year_match = re.search(r'\b(20\d{2})\b', message)
        if tax_year_match and not case_file.user_profile.tax_year:
            case_file.user_profile.tax_year = int(tax_year_match.group(1))

        # Extract income types
        income_keywords = ['salary', 'wages', 'dividend', 'interest', 'rental', 'business', 'freelance', 'pension', 'social security']
        for keyword in income_keywords:
            if keyword in message_lower and keyword not in case_file.user_profile.sources_of_income:
                case_file.user_profile.sources_of_income.append(keyword)
                case_file.income_types.append(keyword)

        # Extract assets
        asset_keywords = ['property', 'real estate', 'stocks', 'bonds', 'bank account', 'investment', 'cryptocurrency', 'business ownership']
        for keyword in asset_keywords:
            if keyword in message_lower and keyword not in case_file.user_profile.foreign_assets:
                case_file.user_profile.foreign_assets.append(keyword)

    def _extract_countries(self, message: str) -> list:
        countries = []
        country_keywords = {
            'us': 'United States', 'usa': 'United States', 'united states': 'United States', 'america': 'United States',
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
            if keyword in message_lower:
                countries.append(country)

        return list(set(countries))

    def _update_conversation_phase(self, case_file: CaseFile) -> None:
        profile = case_file.user_profile

        # Check if basic intake info is complete
        has_countries = len(profile.countries_involved) >= 2
        has_income = len(profile.sources_of_income) > 0
        has_tax_year = profile.tax_year is not None

        basic_complete = has_countries and has_income and has_tax_year

        # Count assistant questions (rough heuristic for clarifications phase)
        assistant_questions = sum(1 for msg in case_file.messages if msg.role.value == "assistant" and "?" in msg.content)

        if case_file.conversation_phase == ConversationPhase.INTAKE and basic_complete:
            case_file.conversation_phase = ConversationPhase.CLARIFICATIONS
        elif case_file.conversation_phase == ConversationPhase.CLARIFICATIONS and assistant_questions >= 2:
            # After at least 2 clarifying questions, ready for final suggestions
            pass  # Stay in clarifications until explicitly moved to final

    def can_provide_final_suggestions(self, case_file: CaseFile) -> bool:
        profile = case_file.user_profile

        # Must have basic info
        has_countries = len(profile.countries_involved) >= 2
        has_income = len(profile.sources_of_income) > 0
        has_tax_year = profile.tax_year is not None

        # Must have asked clarifying questions
        assistant_questions = sum(1 for msg in case_file.messages if msg.role.value == "assistant" and "?" in msg.content)

        return has_countries and has_income and has_tax_year and assistant_questions >= 1