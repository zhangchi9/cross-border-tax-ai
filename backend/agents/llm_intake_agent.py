"""
LLM-based Intake Agent
Handles interactive client consultation and tag assignment using LLM
"""
import json
import re
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from datetime import datetime
import google.generativeai as genai
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_agent import TaxAgent
from app.config import settings


class LLMIntakeAgent(TaxAgent):
    """LLM-powered agent for conducting client intake and assigning tags"""

    def __init__(self):
        super().__init__("llm_intake_agent", "intake/questions.json")
        self.model_provider = settings.AI_MODEL_PROVIDER

        # Initialize the appropriate AI client
        if self.model_provider == "openai":
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model_name = settings.OPENAI_MODEL
        elif self.model_provider == "gemini":
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self.model_name = settings.GEMINI_MODEL
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

        self.conversation_state = {
            "current_module": None,
            "completed_modules": [],
            "assigned_tags": [],
            "client_profile": {},
            "conversation_history": []
        }

    def _get_system_prompt(self) -> str:
        """Get the system prompt for intake agent"""

        # Load gating questions and modules from knowledge base
        gating_questions = self.knowledge_base.get("gating_questions", {}).get("questions", [])
        modules = self.knowledge_base.get("modules", {})

        gating_questions_text = "\n".join([
            f"- {q['question']} → {q.get('action', 'N/A')}"
            for q in gating_questions
        ])

        # Format modules with their questions and tags
        modules_text = ""
        for module_name, module_data in modules.items():
            module_title = module_data.get("title", module_name)
            module_questions = module_data.get("questions", [])
            modules_text += f"\n**{module_title}**:\n"
            for q in module_questions[:3]:  # Show first 3 questions as examples
                action = q.get('action', '')
                if 'add tag:' in action:
                    tag = action.split('add tag:')[1].strip()
                    modules_text += f"  - {q['question']} → TAG: {tag}\n"
                else:
                    modules_text += f"  - {q['question']}\n"

        current_module = self.conversation_state.get('current_module')
        current_module_info = ""
        if current_module and current_module in modules:
            current_questions = modules[current_module].get("questions", [])
            current_module_info = f"\nCURRENT MODULE QUESTIONS:\n"
            for q in current_questions:
                action = q.get('action', '')
                if 'add tag:' in action:
                    tag = action.split('add tag:')[1].strip()
                    current_module_info += f"- {q['question']} → TAG: {tag}\n"

        return f"""You are a specialized cross-border tax intake agent. You MUST follow this EXACT workflow:

**CRITICAL RULE: ASK ONLY ONE QUESTION AT A TIME. NEVER ASK MULTIPLE QUESTIONS IN A SINGLE RESPONSE.**

**PHASE 1: GATING QUESTIONS** (You MUST start here)
{gating_questions_text}

**PHASE 2: MODULE-SPECIFIC QUESTIONS** (Only after gating questions route you to modules)
{modules_text}

{current_module_info}

**MANDATORY WORKFLOW:**
1. **ALWAYS START WITH ONE GATING QUESTION**: Pick the most relevant gating question from the list above
2. **ONE QUESTION ONLY**: Never ask multiple questions in one response
3. **WAIT FOR RESPONSE**: Get client answer before proceeding
4. **ROUTE TO MODULE**: If gating question triggers a module, announce transition
5. **MODULE QUESTIONS**: Ask one question at a time from the specific module
6. **TAG ASSIGNMENT**: Assign exact tags when criteria are met

**RESPONSE FORMAT - YOU MUST FOLLOW THIS EXACTLY:**
- Ask ONE gating question (if in gating phase)
- OR ask ONE module question (if in module phase)
- Include appropriate quick replies
- Assign tags only when specific criteria are clearly met

**CURRENT STATE:**
- Phase: {"Gating Questions - ASK ONE GATING QUESTION NOW" if not current_module else f"Module: {current_module} - ASK ONE MODULE QUESTION"}
- Assigned Tags: {self.conversation_state.get('assigned_tags', [])}

**EXAMPLE CORRECT RESPONSE:**
"Are you a U.S. citizen or U.S. green-card holder?"
QUICK_REPLIES: ["Yes", "No", "Not sure"]

**DO NOT:**
- Ask multiple questions at once
- Ask general intake questions
- Skip the gating questions
- Make up your own questions

**TAG FORMAT:**
ASSIGNED_TAGS: ["exact_tag_from_knowledge_base"]

**SAFETY:**
- Never ask for SSN, SIN, passport numbers
- Stick to the structured workflow exactly
"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method for client interaction"""
        client_message = input_data.get("message", "")
        session_context = input_data.get("session_context", {})

        # Update conversation state from session
        if "conversation_state" in session_context:
            self.conversation_state.update(session_context["conversation_state"])

        # Debug log to check state
        self.logger.info(f"Current conversation state: {self.conversation_state}")
        self.logger.info(f"Current module: {self.conversation_state.get('current_module')}")
        self.logger.info(f"Assigned tags: {self.conversation_state.get('assigned_tags', [])}")

        # Add message to history
        self.conversation_state["conversation_history"].append({
            "speaker": "client",
            "message": client_message,
            "timestamp": datetime.now().isoformat()
        })

        # Generate LLM response
        response = await self._generate_llm_response(client_message)

        # Extract tags and quick replies from response
        clean_response, assigned_tags, quick_replies = self._parse_llm_response(response)

        # Debug: Check if LLM violated one question rule and fix it
        question_count = clean_response.count('?')
        numbered_lists = len([line for line in clean_response.split('\n') if re.match(r'^\s*\d+\.', line)])

        if question_count > 1 or numbered_lists > 1:
            self.logger.warning(f"LLM violated one question rule! Questions: {question_count}, Numbered items: {numbered_lists}")
            self.logger.warning(f"Original response: {clean_response[:200]}...")

            # Fix the violation by extracting just the first question
            clean_response = self._fix_multiple_questions_response(clean_response)
            self.logger.info(f"Fixed response: {clean_response}")

            # Regenerate quick replies for the single question
            if '?' in clean_response:
                quick_replies = ["Yes", "No", "Not sure"]

        # Update assigned tags
        if assigned_tags:
            for tag in assigned_tags:
                if tag not in self.conversation_state["assigned_tags"]:
                    self.conversation_state["assigned_tags"].append(tag)

        # Update module progression based on conversation
        self._update_module_progression(client_message, clean_response)

        # Add agent response to history
        self.conversation_state["conversation_history"].append({
            "speaker": "agent",
            "message": clean_response,
            "timestamp": datetime.now().isoformat()
        })

        # Determine if we should transition to forms analysis
        should_transition = self._should_transition_to_forms_analysis()

        result = {
            "message": clean_response,
            "assigned_tags": self.conversation_state["assigned_tags"],
            "quick_replies": quick_replies,
            "session_context": {
                "conversation_state": self.conversation_state
            },
            "transition": should_transition,
            "question_type": "intake"
        }

        if should_transition:
            result["handoff_data"] = {
                "tags": self.conversation_state["assigned_tags"],
                "client_profile": self.conversation_state["client_profile"],
                "case_summary": self._generate_case_summary()
            }

        return result

    async def _generate_llm_response(self, client_message: str) -> str:
        """Generate response using LLM"""
        # Build conversation history for context
        history_text = ""
        for entry in self.conversation_state["conversation_history"][-10:]:  # Last 10 messages
            speaker = entry["speaker"].title()
            history_text += f"{speaker}: {entry['message']}\n"

        # Determine current phase and guidance
        current_module = self.conversation_state.get("current_module")
        completed_modules = self.conversation_state.get("completed_modules", [])
        assigned_tags = self.conversation_state.get("assigned_tags", [])

        if not current_module and len(completed_modules) == 0:
            # Get list of gating questions for explicit reference
            gating_questions = self.knowledge_base.get("gating_questions", {}).get("questions", [])
            available_questions = "\n".join([f"- {q['question']}" for q in gating_questions[:5]])

            phase_guidance = f"""
🚨 CRITICAL: YOU ARE IN GATING QUESTIONS PHASE 🚨

**YOU MUST ASK ONE GATING QUESTION NOW. NO EXCEPTIONS.**

Available gating questions:
{available_questions}

INSTRUCTIONS:
- Pick ONE gating question from the list above
- Ask ONLY that one question
- Do NOT ask multiple questions
- Do NOT ask general intake questions
- Do NOT make up your own questions

EXAMPLE RESPONSE:
"Are you a U.S. citizen or U.S. green-card holder?"
QUICK_REPLIES: ["Yes", "No", "Not sure"]
"""
        elif current_module:
            modules = self.knowledge_base.get("modules", {})
            module_questions = modules.get(current_module, {}).get("questions", [])
            module_guidance = f"""
CURRENT PHASE: MODULE {current_module.upper()}
- Ask specific questions from this module to assign precise tags
- Available questions for this module:
"""
            for q in module_questions[:5]:  # Show first 5 questions
                action = q.get('action', '')
                if 'add tag:' in action:
                    tag = action.split('add tag:')[1].strip()
                    module_guidance += f"  • {q['question']} → TAG: {tag}\n"
            phase_guidance = module_guidance
        else:
            phase_guidance = """
CURRENT PHASE: TRANSITION
- You may need to ask gating questions for other areas
- Or transition to forms analysis if enough information is gathered
"""

        prompt = f"""
CONVERSATION HISTORY:
{history_text}

CURRENT CLIENT MESSAGE: {client_message}

{phase_guidance}

🔴 CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. You MUST ask ONLY ONE question in your response
2. If you're in gating questions phase, pick ONE gating question from the knowledge base
3. If you're in module phase, ask ONE module-specific question
4. NEVER list multiple questions or create a questionnaire
5. NEVER ask "Could you please provide the following information?" followed by multiple questions

❌ WRONG RESPONSE EXAMPLE:
"Thank you for sharing that. To better understand your tax situation, could you please provide the following information? 1. What is your tax residency status... 2. What countries are involved... 3. What is your filing status..."

✅ CORRECT RESPONSE EXAMPLE:
"Are you a U.S. citizen or U.S. green-card holder?"
QUICK_REPLIES: ["Yes", "No", "Not sure"]

Current State:
- Phase: {current_module or "GATING QUESTIONS"}
- Assigned Tags: {assigned_tags}
- Completed Modules: {completed_modules}

YOUR RESPONSE MUST CONTAIN EXACTLY ONE QUESTION.
"""

        try:
            if self.model_provider == "openai":
                messages = [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]

                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.1,  # Lower temperature for more deterministic behavior
                    max_tokens=300,   # Shorter responses to force focus
                    top_p=0.1        # More focused responses
                )

                return response.choices[0].message.content

            elif self.model_provider == "gemini":
                full_prompt = f"{self._get_system_prompt()}\n\n{prompt}"
                response = self.model.generate_content(full_prompt)
                return response.text

        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            self.logger.error(f"Model provider: {self.model_provider}")
            self.logger.error(f"Model name: {self.model_name}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return "I apologize, but I'm having trouble processing your request. Could you please try again?"

    def _parse_llm_response(self, response: str) -> Tuple[str, List[str], List[str]]:
        """Parse LLM response to extract tags and quick replies"""
        # Extract assigned tags
        tags_match = re.search(r'ASSIGNED_TAGS:\s*\[(.*?)\]', response, re.IGNORECASE | re.DOTALL)
        assigned_tags = []
        if tags_match:
            tags_str = tags_match.group(1)
            # Parse JSON-like list
            try:
                tags_str = f"[{tags_str}]"
                assigned_tags = json.loads(tags_str)
            except:
                # Fallback to simple parsing
                assigned_tags = [tag.strip().strip('"\'') for tag in tags_str.split(',') if tag.strip()]

        # Extract quick replies
        quick_replies_match = re.search(r'QUICK_REPLIES:\s*\[(.*?)\]', response, re.IGNORECASE | re.DOTALL)
        quick_replies = []
        if quick_replies_match:
            replies_str = quick_replies_match.group(1)
            try:
                replies_str = f"[{replies_str}]"
                quick_replies = json.loads(replies_str)
            except:
                # Fallback to simple parsing
                quick_replies = [reply.strip().strip('"\'') for reply in replies_str.split(',') if reply.strip()]

        # Clean response by removing the extracted parts
        clean_response = response
        if tags_match:
            clean_response = clean_response.replace(tags_match.group(0), '').strip()
        if quick_replies_match:
            clean_response = clean_response.replace(quick_replies_match.group(0), '').strip()

        return clean_response, assigned_tags, quick_replies

    def _fix_multiple_questions_response(self, response: str) -> str:
        """Fix responses that contain multiple questions by extracting just the first appropriate question"""

        # First check if we're in gating questions phase
        current_module = self.conversation_state.get('current_module')

        if not current_module:
            # We should be asking gating questions - extract or generate appropriate gating question
            gating_questions = self.knowledge_base.get("gating_questions", {}).get("questions", [])

            # Try to find a gating question in the response
            for gating_q in gating_questions:
                question_text = gating_q["question"]
                if question_text.lower() in response.lower():
                    return question_text

            # If no gating question found, default to the first one
            if gating_questions:
                return gating_questions[0]["question"]

        # If we're in a module, try to extract first valid question
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if '?' in line and not line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.')):
                # Clean up the line
                line = re.sub(r'^\d+\.\s*', '', line)  # Remove numbering
                line = re.sub(r'^[•\-]\s*', '', line)  # Remove bullet points
                if len(line) > 10:  # Reasonable question length
                    return line

        # Fallback: return a default gating question
        return "Are you a U.S. citizen or U.S. green-card holder?"

    def _update_module_progression(self, client_message: str, agent_response: str) -> None:
        """Update module progression based on conversation flow"""
        # Check if agent is transitioning to a specific module
        agent_lower = agent_response.lower()

        # Module mapping from response text
        module_mappings = {
            "residency": "residency_elections",
            "employment": "employment_states",
            "business": "business_entities",
            "real estate": "real_estate",
            "investment": "investments_financial",
            "pension": "pensions_savings",
            "equity": "equity_compensation",
            "estate": "estates_gifts_trusts",
            "reporting": "reporting_cleanup"
        }

        # Check if transitioning to a module
        for keyword, module_id in module_mappings.items():
            if keyword in agent_lower and ("module" in agent_lower or "questions about" in agent_lower):
                if module_id not in self.conversation_state["completed_modules"]:
                    self.conversation_state["current_module"] = module_id
                    self.logger.info(f"Transitioned to module: {module_id}")
                break

        # Check if module is complete (when agent asks about different topic or says "moving on")
        if self.conversation_state.get("current_module"):
            if any(phrase in agent_lower for phrase in ["moving on", "next topic", "different area", "other questions"]):
                completed_module = self.conversation_state["current_module"]
                if completed_module not in self.conversation_state["completed_modules"]:
                    self.conversation_state["completed_modules"].append(completed_module)
                self.conversation_state["current_module"] = None
                self.logger.info(f"Completed module: {completed_module}")

    def _should_ask_gating_questions(self) -> bool:
        """Determine if we should still be asking gating questions"""
        # Ask gating questions if no module has been identified and few tags assigned
        return (not self.conversation_state.get("current_module") and
                len(self.conversation_state.get("assigned_tags", [])) < 2 and
                len(self.conversation_state.get("completed_modules", [])) == 0)

    def _should_transition_to_forms_analysis(self) -> bool:
        """Determine if we should transition to forms analysis"""
        # Transition when we have sufficient tags and information
        min_tags_threshold = 2  # Minimum number of tags to proceed
        conversation_length = len(self.conversation_state["conversation_history"])

        has_sufficient_tags = len(self.conversation_state["assigned_tags"]) >= min_tags_threshold
        has_sufficient_conversation = conversation_length >= 6  # At least 3 exchanges

        return has_sufficient_tags and has_sufficient_conversation

    def _generate_case_summary(self) -> str:
        """Generate a brief case summary for handoff to forms analysis agent"""
        tags = self.conversation_state["assigned_tags"]

        if not tags:
            return "Client intake completed with basic information gathered."

        return f"Client has been identified with the following tax considerations: {', '.join(tags)}. Ready for forms analysis and compliance assessment."

    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary"""
        return {
            "assigned_tags": self.conversation_state["assigned_tags"],
            "current_module": self.conversation_state["current_module"],
            "completed_modules": self.conversation_state["completed_modules"],
            "conversation_length": len(self.conversation_state["conversation_history"]),
            "forms_analysis_ready": self._should_transition_to_forms_analysis()
        }