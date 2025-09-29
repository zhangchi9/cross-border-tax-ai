"""
LangGraph Nodes for Tax Consultation Workflow
"""
import json
import re
from typing import Dict, Any, List, Tuple
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.config import settings
from .state import TaxConsultationState, add_message_to_state, get_conversation_context, update_state_timestamp


class BaseNode:
    """Base class for all workflow nodes"""

    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.llm = self._initialize_llm()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base files"""
        try:
            kb_path = Path(__file__).parent.parent / "data" / "knowledge_base"

            # Load intake questions
            intake_path = kb_path / "intake" / "questions.json"
            with open(intake_path, 'r', encoding='utf-8') as f:
                intake_data = json.load(f)

            # Load tag definitions
            tags_path = kb_path / "tags" / "definitions.json"
            with open(tags_path, 'r', encoding='utf-8') as f:
                tags_data = json.load(f)

            return {
                "intake": intake_data,
                "tags": tags_data
            }

        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            return {}

    def _initialize_llm(self):
        """Initialize the LLM based on configuration"""
        if settings.AI_MODEL_PROVIDER == "openai":
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.1,
                api_key=settings.OPENAI_API_KEY
            )
        elif settings.AI_MODEL_PROVIDER == "gemini":
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                temperature=0.1,
                google_api_key=settings.GEMINI_API_KEY
            )
        else:
            raise ValueError(f"Unsupported AI model provider: {settings.AI_MODEL_PROVIDER}")


class IntakeNode(BaseNode):
    """Node for handling intake questions and tag assignment"""

    def __call__(self, state: TaxConsultationState) -> TaxConsultationState:
        """Process intake phase"""

        try:
            # Update knowledge base context in state
            state["knowledge_base"] = self.knowledge_base
            state["available_gating_questions"] = self.knowledge_base.get("intake", {}).get("gating_questions", {}).get("questions", [])

            # Add user message to conversation
            if state["current_message"]:
                state = add_message_to_state(state, "user", state["current_message"])

            # Generate assistant response
            response, quick_replies, new_tags = self._generate_intake_response(state)

            # Update state with response
            state["assistant_response"] = response
            state["quick_replies"] = quick_replies

            # Add assistant message to conversation
            state = add_message_to_state(state, "assistant", response)

            # Update assigned tags
            for tag in new_tags:
                if tag not in state["assigned_tags"]:
                    state["assigned_tags"].append(tag)

            # Update module progression
            state = self._update_module_progression(state, response)

            # Check if we should transition to forms analysis
            state = self._check_transition_conditions(state)

            # Ensure we stay in intake phase unless explicitly transitioning
            if not state.get("should_transition", False):
                state["current_phase"] = "intake"

            state = update_state_timestamp(state)

            return state

        except Exception as e:
            state["error_message"] = f"Intake processing error: {str(e)}"
            state["assistant_response"] = "I apologize, but I'm having trouble processing your request. Could you please try again?"
            return state

    def _generate_intake_response(self, state: TaxConsultationState) -> Tuple[str, List[str], List[str]]:
        """Generate response using LLM"""

        # Build system prompt
        system_prompt = self._build_intake_system_prompt(state)

        # Build user prompt with conversation context
        conversation_context = get_conversation_context(state)
        user_prompt = f"""
CONVERSATION HISTORY:
{conversation_context}

CURRENT CLIENT MESSAGE: {state["current_message"]}

CURRENT STATE:
- Phase: {state["current_phase"]}
- Current Module: {state["current_module"] or "Gating Questions"}
- Assigned Tags: {state["assigned_tags"]}
- Completed Modules: {state["completed_modules"]}

INSTRUCTIONS:
1. Ask ONLY ONE question at a time
2. If in gating questions phase, pick ONE gating question from the knowledge base
3. If in module phase, ask ONE module-specific question
4. Assign tags exactly as specified in the knowledge base when criteria are met
5. Follow the structured workflow: Gating Questions → Module Questions → Tag Assignment

YOUR RESPONSE MUST CONTAIN EXACTLY ONE QUESTION.
"""

        # Generate response using LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        content = response.content

        # Parse response for tags and quick replies
        clean_response, assigned_tags, quick_replies = self._parse_response(content)

        # Fix multiple questions if LLM violated the rule
        if self._has_multiple_questions(clean_response):
            clean_response = self._fix_multiple_questions(clean_response, state)
            quick_replies = ["Yes", "No", "Not sure"]

        return clean_response, quick_replies, assigned_tags

    def _build_intake_system_prompt(self, state: TaxConsultationState) -> str:
        """Build system prompt for intake phase"""

        gating_questions = state["available_gating_questions"]
        gating_questions_text = "\n".join([
            f"- {q['question']} → {q.get('action', 'N/A')}"
            for q in gating_questions
        ])

        current_module = state["current_module"]
        current_module_info = ""

        if current_module:
            modules = self.knowledge_base.get("intake", {}).get("modules", {})
            if current_module in modules:
                module_questions = modules[current_module].get("questions", [])
                current_module_info = f"\nCURRENT MODULE QUESTIONS:\n"
                for q in module_questions[:5]:  # Show first 5
                    action = q.get('action', '')
                    if 'add tag:' in action:
                        tag = action.split('add tag:')[1].strip()
                        current_module_info += f"- {q['question']} → TAG: {tag}\n"

        return f"""You are a specialized cross-border tax intake agent. You MUST follow this EXACT workflow:

**CRITICAL RULE: ASK ONLY ONE QUESTION AT A TIME. NEVER ASK MULTIPLE QUESTIONS IN A SINGLE RESPONSE.**

**PHASE 1: GATING QUESTIONS** (You MUST start here)
{gating_questions_text}

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

**EXAMPLE CORRECT RESPONSE:**
"Are you a U.S. citizen or U.S. green-card holder?"
QUICK_REPLIES: ["Yes", "No", "Not sure"]

**TAG FORMAT:**
ASSIGNED_TAGS: ["exact_tag_from_knowledge_base"]

**SAFETY:**
- Never ask for SSN, SIN, passport numbers
- Stick to the structured workflow exactly
"""

    def _parse_response(self, response: str) -> Tuple[str, List[str], List[str]]:
        """Parse LLM response to extract tags and quick replies"""

        # Extract assigned tags
        tags_match = re.search(r'ASSIGNED_TAGS:\s*\[(.*?)\]', response, re.IGNORECASE | re.DOTALL)
        assigned_tags = []
        if tags_match:
            tags_str = tags_match.group(1)
            try:
                tags_str = f"[{tags_str}]"
                assigned_tags = json.loads(tags_str)
            except:
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
                quick_replies = [reply.strip().strip('"\'') for reply in replies_str.split(',') if reply.strip()]

        # Clean response by removing the extracted parts
        clean_response = response
        if tags_match:
            clean_response = clean_response.replace(tags_match.group(0), '').strip()
        if quick_replies_match:
            clean_response = clean_response.replace(quick_replies_match.group(0), '').strip()

        return clean_response, assigned_tags, quick_replies

    def _has_multiple_questions(self, response: str) -> bool:
        """Check if response has multiple questions"""
        question_count = response.count('?')
        numbered_lists = len([line for line in response.split('\n') if re.match(r'^\s*\d+\.', line)])
        return question_count > 1 or numbered_lists > 1

    def _fix_multiple_questions(self, response: str, state: TaxConsultationState) -> str:
        """Fix responses with multiple questions by extracting appropriate single question"""

        current_module = state["current_module"]

        if not current_module:
            # Should be asking gating questions
            gating_questions = state["available_gating_questions"]
            for gating_q in gating_questions:
                question_text = gating_q["question"]
                if question_text.lower() in response.lower():
                    return question_text
            # Default to first gating question
            if gating_questions:
                return gating_questions[0]["question"]

        # Extract first reasonable question
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if '?' in line and not line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.')):
                line = re.sub(r'^\d+\.\s*', '', line)
                line = re.sub(r'^[•\-]\s*', '', line)
                if len(line) > 10:
                    return line

        # Fallback
        return "Are you a U.S. citizen or U.S. green-card holder?"

    def _update_module_progression(self, state: TaxConsultationState, agent_response: str) -> TaxConsultationState:
        """Update module progression based on conversation flow"""

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
                if module_id not in state["completed_modules"]:
                    state["current_module"] = module_id
                break

        # Check if module is complete
        if state["current_module"]:
            if any(phrase in agent_lower for phrase in ["moving on", "next topic", "different area", "other questions"]):
                completed_module = state["current_module"]
                if completed_module not in state["completed_modules"]:
                    state["completed_modules"].append(completed_module)
                state["current_module"] = None

        return state

    def _check_transition_conditions(self, state: TaxConsultationState) -> TaxConsultationState:
        """Check if we should transition to forms analysis"""

        min_tags_threshold = 2
        conversation_length = len(state["messages"])

        has_sufficient_tags = len(state["assigned_tags"]) >= min_tags_threshold
        has_sufficient_conversation = conversation_length >= 6

        # Only transition with sufficient information - never force transition in initial conversations
        if has_sufficient_tags and has_sufficient_conversation:
            state["should_transition"] = True
            state["transition_reason"] = "Sufficient information gathered for forms analysis"
            state["current_phase"] = "forms_analysis"

        return state


class FormsAnalysisNode(BaseNode):
    """Node for forms analysis based on assigned tags"""

    def __call__(self, state: TaxConsultationState) -> TaxConsultationState:
        """Process forms analysis phase"""

        try:
            # Generate forms analysis
            analysis_result = self._generate_forms_analysis(state)

            # Update state with analysis results
            state["required_forms"] = analysis_result.get("required_forms", [])
            state["compliance_checklist"] = analysis_result.get("compliance_checklist", [])
            state["estimated_complexity"] = analysis_result.get("estimated_complexity", "medium")
            state["recommendations"] = analysis_result.get("recommendations", [])
            state["next_steps"] = analysis_result.get("next_steps", [])
            state["priority_deadlines"] = analysis_result.get("priority_deadlines", [])

            # Format comprehensive response
            response = self._format_analysis_response(analysis_result)
            state["assistant_response"] = response

            # Add to conversation
            state = add_message_to_state(state, "assistant", response)

            # Mark as completed
            state["current_phase"] = "completed"
            state = update_state_timestamp(state)

            return state

        except Exception as e:
            state["error_message"] = f"Forms analysis error: {str(e)}"
            state["assistant_response"] = "I apologize, but I encountered an error during forms analysis. Please consult with a tax professional."
            return state

    def _generate_forms_analysis(self, state: TaxConsultationState) -> Dict[str, Any]:
        """Generate forms analysis using LLM"""

        tags = state["assigned_tags"]
        if not tags:
            return {"required_forms": [], "recommendations": ["Please complete the intake process first."]}

        # Build system prompt with tag definitions
        tag_definitions = self.knowledge_base.get("tags", {}).get("tag_definitions", {})
        tags_text = ""
        for tag_name, tag_info in tag_definitions.items():
            if tag_name in tags:
                description = tag_info.get("description", "No description")
                forms = tag_info.get("forms", {})
                tags_text += f"\n**{tag_name}**: {description}\n"
                if forms:
                    for jurisdiction, form_list in forms.items():
                        tags_text += f"  - {jurisdiction}: {', '.join(form_list)}\n"

        system_prompt = f"""You are a specialized cross-border tax forms analysis agent. Analyze the provided tags and determine required tax forms and compliance obligations.

KNOWLEDGE BASE - RELEVANT TAG DEFINITIONS:
{tags_text}

Your task is to provide a comprehensive forms analysis in JSON format:

{{
    "analysis_summary": "Brief overview of the analysis",
    "required_forms": [
        {{
            "form": "Form Name",
            "jurisdiction": "US/Canada/State",
            "priority": "high/medium/low",
            "due_date": "YYYY-MM-DD or description",
            "description": "What this form is for"
        }}
    ],
    "estimated_complexity": "high/medium/low",
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "next_steps": ["Action item 1", "Action item 2"],
    "priority_deadlines": [
        {{
            "form": "Form Name",
            "jurisdiction": "US/Canada",
            "due_date": "YYYY-MM-DD or description"
        }}
    ],
    "compliance_checklist": [
        {{
            "task": "Task description",
            "due_date": "YYYY-MM-DD or description",
            "status": "pending"
        }}
    ]
}}

Be comprehensive but practical. Focus on compliance and accuracy.
"""

        user_prompt = f"""
ASSIGNED TAGS: {', '.join(tags)}

Please analyze these tags and provide a comprehensive forms analysis using the knowledge base. Focus on:
1. Required tax forms based on these specific tags
2. Priorities and deadlines
3. Overall complexity assessment
4. Actionable recommendations
5. Next steps for compliance

Provide your analysis in the JSON format specified in the system prompt.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        content = response.content

        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                analysis_result = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

            return analysis_result

        except Exception as e:
            # Fallback analysis
            return {
                "analysis_summary": f"Analysis for tags: {', '.join(tags)}. Please consult a tax professional for detailed requirements.",
                "required_forms": [],
                "estimated_complexity": "high",
                "recommendations": ["Consult with a qualified tax professional", "Gather all relevant tax documents"],
                "next_steps": ["Schedule consultation with tax professional"],
                "priority_deadlines": [],
                "compliance_checklist": []
            }

    def _format_analysis_response(self, analysis: Dict[str, Any]) -> str:
        """Format analysis results into comprehensive response"""

        sections = []

        # Analysis summary
        summary = analysis.get("analysis_summary", "")
        if summary:
            sections.append(f"## Analysis Summary\n\n{summary}")

        # Required forms
        required_forms = analysis.get("required_forms", [])
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
        complexity = analysis.get("estimated_complexity", "")
        if complexity:
            complexity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(complexity, "🟢")
            sections.append(f"## Complexity Assessment\n\n{complexity_emoji} **{complexity.title()} Complexity**")

        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            sections.append("## Key Recommendations")
            for i, rec in enumerate(recommendations, 1):
                sections.append(f"{i}. {rec}")

        # Next steps
        next_steps = analysis.get("next_steps", [])
        if next_steps:
            sections.append("## Immediate Next Steps")
            for i, step in enumerate(next_steps, 1):
                sections.append(f"{i}. {step}")

        return "\n\n".join(sections)


class CompletionNode(BaseNode):
    """Node for handling completion and follow-up questions"""

    def __call__(self, state: TaxConsultationState) -> TaxConsultationState:
        """Handle completion phase"""

        if state["current_message"]:
            # User has a follow-up question
            response = "Your forms analysis has been completed. If you have specific questions about the recommendations or need clarification on any forms, please ask and I'll help clarify."

            state["assistant_response"] = response
            state = add_message_to_state(state, "user", state["current_message"])
            state = add_message_to_state(state, "assistant", response)

        state = update_state_timestamp(state)
        return state