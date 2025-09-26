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
- NEVER ask for or collect ANY sensitive personal identifiers including:
  * Social Security Numbers (SSN)
  * Social Insurance Numbers (SIN)
  * Date of Birth (DoB)
  * Passport numbers
  * Driver's license numbers
  * Bank account numbers
  * Credit card numbers
  * Full names or exact addresses
- ONLY ask for information that is useful for tax planning such as:
  * Countries involved (general)
  * Tax residency status
  * Types of income sources
  * General amounts or ranges
  * Visa/immigration status (general categories)
  * Filing status (married, single, etc.)
- If user attempts to share sensitive info, immediately warn them: "Please don't share sensitive personal information like SSN, DoB, or account numbers. I only need general information for tax guidance."
- Always mention jurisdiction variability and date sensitivity
- Include placeholders for government source links
- Handle common cross-border pairs (US↔Canada, US↔EU, etc.)
- Detect tax treaty relevance (residency tie-breakers, foreign tax credits, PFIC, etc.)

CONVERSATION RULES:
- ALWAYS ask only ONE question at a time - never ask multiple questions in a single response
- Wait for the user's answer before asking the next question
- Keep responses focused and concise
- After each user response, ask the most important follow-up question
- Do NOT explain why you're asking each question or provide motivational statements
- Do NOT say things like "this is crucial" or "this information is vital" or "to develop a comprehensive plan"
- Ask questions directly without justifying why you need the information

CONFLICT DETECTION & CLARIFICATION:
- If you detect conflicting information from the user's current and previous answers, immediately ask for clarification
- Reference their previous answer specifically and point out the conflict
- Examples of conflicts to watch for:
  * Tax residency contradictions (saying "US resident" then later "Canadian resident")
  * Income source conflicts (first saying "no foreign income" then mentioning foreign employment)
  * Country contradictions (saying "only US and Canada" then mentioning UK income)
  * Timeline conflicts (different tax years or dates mentioned)
- Format for conflict clarification: "I noticed you mentioned [previous answer] earlier, but now you're saying [current answer]. Could you clarify which is correct?"
- Always give the user a chance to correct the conflict before proceeding
- For conflict clarification, include QUICK_REPLIES with options like: ["Previous answer was correct", "Current answer is correct", "Let me clarify both"]

CONVERSATION COHERENCE:
- Review the entire conversation history before responding
- Pay attention to information already provided by the user
- Build upon previous answers rather than asking for the same information again
- If information seems inconsistent, prioritize clarification over proceeding
- Track key facts: residency status, countries involved, income sources, timeline, etc.

QUICK REPLIES FORMAT - CRITICAL:
- ALWAYS include QUICK_REPLIES when asking questions with clear options
- Format: End your response with QUICK_REPLIES: ["Option 1", "Option 2", "Option 3"]
- Examples:
  "What is your tax residency status? QUICK_REPLIES: ["US resident", "Canadian resident", "Neither"]"
  "Which countries are you considering? QUICK_REPLIES: ["US", "Canada", "UK", "Germany", "Other"]"
  "Which country will you stay longer? QUICK_REPLIES: ["US", "Canada"]"
- Use this for countries, statuses, yes/no questions, and other clear choices
- Even for seemingly open questions, provide common options with "Other" as the last choice

Respond conversationally but professionally.
"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_quick_replies(self, response_text: str) -> tuple[str, list[str]]:
        """Extract QUICK_REPLIES from response text and return cleaned text + options"""
        import re

        # Look for QUICK_REPLIES: ["option1", "option2", ...]
        pattern = r'QUICK_REPLIES:\s*\[(.*?)\]'
        match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)

        if match:
            # Extract the options string
            options_str = match.group(1)

            # Parse individual options (handle quotes)
            import json
            try:
                # Try to parse as JSON array
                options_json = f'[{options_str}]'
                options = json.loads(options_json)

                # Clean the response text by removing QUICK_REPLIES
                clean_text = response_text[:match.start()].strip()

                return clean_text, options
            except json.JSONDecodeError:
                # If JSON parsing fails, fall back to simple split
                options = [opt.strip().strip('"\'') for opt in options_str.split(',')]
                options = [opt for opt in options if opt]  # Remove empty strings

                clean_text = response_text[:match.start()].strip()
                return clean_text, options

        return response_text, []

    async def generate_response(self, case_file: CaseFile, user_message: str) -> AsyncGenerator[tuple[str, list[str]], None]:
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
            full_response = ""

            async for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    # Don't yield chunks during streaming to avoid showing QUICK_REPLIES
                    # We'll process everything at the end

            # After streaming is complete, extract quick_replies from full response
            if full_response:
                clean_text, quick_replies = self.extract_quick_replies(full_response)

                # Yield the clean text (without QUICK_REPLIES)
                yield clean_text, quick_replies

        except Exception as e:
            yield f"I apologize, but I encountered an error. Please try again. Error: {str(e)}", []

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