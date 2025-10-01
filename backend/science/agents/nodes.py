"""
LangGraph Nodes for Tax Consultation Workflow

Owner: Science Team

These nodes define the AI behavior at each phase of the consultation workflow.
"""
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from science.services.llm_service import get_llm
from science.config import science_config
from .state import TaxConsultationState, add_message_to_state, get_conversation_context, update_state_timestamp
from .prompts import (
    build_intake_system_prompt,
    build_intake_user_prompt,
    build_forms_analysis_system_prompt,
    build_forms_analysis_user_prompt,
    build_tag_analysis_prompt,
    build_question_selection_prompt,
    build_multi_fact_extraction_prompt,
    build_module_relevance_prompt,
    build_clarification_question_prompt,
    build_follow_up_question_prompt,
    build_explanation_prompt
)


class BaseNode:
    """Base class for all workflow nodes"""

    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.llm = get_llm()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """
        Load knowledge base files from tax_team content

        Note: Science team parses markdown files and caches JSON
        """
        try:
            # Path points to science team's cached output
            kb_path = Path(__file__).parent.parent / "knowledge_cache"

            # Fallback to old location if new structure not ready
            if not kb_path.exists():
                kb_path = Path(__file__).parent.parent.parent / "data" / "knowledge_base"

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


class IntakeNode(BaseNode):
    """Node for handling intake questions and tag assignment"""

    def __init__(self):
        super().__init__()
        # Build module mapping dynamically from knowledge base
        self.gating_to_module_map = self._build_module_mapping()

    def _build_module_mapping(self) -> Dict[str, str]:
        """Build mapping from gating question IDs to module names dynamically"""
        mapping = {}

        # Module name normalization (convert "Module A — Residency & Elections" → "residency_elections")
        module_name_map = {
            "Module A": "residency_elections",
            "Module B": "employment_states",
            "Module C": "business_entities",
            "Module D": "real_estate",
            "Module E": "investments_financial",
            "Module F": "pensions_savings",
            "Module G": "equity_compensation",
            "Module H": "estates_gifts_trusts",
            "Module I": "reporting_cleanup"
        }

        # Extract gating questions from knowledge base
        gating_questions = self.knowledge_base.get("intake", {}).get("gating_questions", {}).get("questions", [])

        for question in gating_questions:
            question_id = question.get("id")
            action = question.get("action", "")

            if question_id and "Go to Module" in action:
                # Extract module reference (e.g., "Module A")
                import re
                module_match = re.search(r'Module ([A-I])', action)
                if module_match:
                    module_letter = f"Module {module_match.group(1)}"
                    if module_letter in module_name_map:
                        mapping[question_id] = module_name_map[module_letter]

        return mapping

    def __call__(self, state: TaxConsultationState) -> TaxConsultationState:
        """Process intake phase"""

        try:
            # Update knowledge base context in state
            state["knowledge_base"] = self.knowledge_base
            state["available_gating_questions"] = self.knowledge_base.get("intake", {}).get("gating_questions", {}).get("questions", [])

            # Phase 3: Check for correction keywords
            if science_config.USE_CONTEXT_CORRECTION and state["current_message"]:
                correction_detected = self._detect_correction(state["current_message"])
                if correction_detected:
                    # Handle correction
                    state = self._handle_correction(state["current_message"], state)

            # Analyze previous response for tags (if there was a question asked)
            tag_analysis_result = None
            if state["current_message"] and len(state["asked_question_ids"]) > 0:
                # Get the last question that was asked
                previous_question_id = state["asked_question_ids"][-1]

                # Find the question object
                all_questions = state["available_gating_questions"].copy()
                modules = self.knowledge_base.get("intake", {}).get("modules", {})
                for module_data in modules.values():
                    all_questions.extend(module_data.get("questions", []))

                previous_question = None
                for q in all_questions:
                    if q.get("id") == previous_question_id:
                        previous_question = q
                        break

                if previous_question:
                    # Use LLM or fallback based on config
                    if science_config.USE_LLM_TAG_ASSIGNMENT:
                        tag_analysis_result = self._analyze_response_with_llm(
                            state["current_message"],
                            previous_question,
                            state
                        )
                    else:
                        # Use deterministic fallback
                        tag_analysis_result = self._analyze_response_for_tags_fallback(
                            state["current_message"],
                            previous_question,
                            state
                        )

                    # Phase 3: Check if clarification is needed
                    if (science_config.USE_AUTO_CLARIFICATION and
                        tag_analysis_result.get("needs_clarification", False)):
                        # Enter clarification mode
                        state["clarification_mode"] = True
                        state["clarification_context"] = {
                            "original_question_id": previous_question_id,
                            "original_response": state["current_message"],
                            "clarification_question": tag_analysis_result.get("clarification_question", ""),
                            "pending_tags": tag_analysis_result.get("assigned_tags", []),
                            "reasoning": tag_analysis_result.get("reasoning", "")
                        }
                        # Don't assign tags yet - wait for clarification
                    else:
                        # Update assigned tags with confidence tracking
                        from datetime import datetime
                        for tag in tag_analysis_result.get("assigned_tags", []):
                            if tag not in state["assigned_tags"]:
                                state["assigned_tags"].append(tag)

                                # Track confidence
                                confidence = tag_analysis_result.get("confidence", {}).get(tag, "medium")
                                state["tag_confidence"][tag] = confidence

                                # Track reasoning for audit trail
                                state["tag_assignment_reasoning"][tag] = {
                                    "question_id": previous_question_id,
                                    "user_response": state["current_message"],
                                    "confidence": confidence,
                                    "reasoning": tag_analysis_result.get("reasoning", ""),
                                    "timestamp": datetime.now().isoformat()
                                }

            # Phase 3: Multi-fact extraction - extract ALL facts from response
            if state["current_message"] and science_config.USE_MULTI_FACT_EXTRACTION:
                extraction_result = self._extract_all_facts_from_response(
                    state["current_message"],
                    state
                )
                # Apply extracted facts with confidence tracking
                state = self._apply_extracted_facts(state, extraction_result)

            # Phase 3: Check if we need adaptive follow-up
            if (science_config.USE_ADAPTIVE_FOLLOWUPS and
                previous_question and
                tag_analysis_result and
                state["follow_up_depth"] < 2):  # Max 2 follow-ups per question

                followup_result = self._check_for_followup(
                    previous_question,
                    state["current_message"],
                    tag_analysis_result.get("assigned_tags", []),
                    state
                )

                if followup_result.get("needs_followup", False):
                    # Set up follow-up context
                    state["clarification_mode"] = True
                    state["clarification_context"] = {
                        "type": "adaptive_followup",
                        "original_question_id": previous_question_id,
                        "followup_question": followup_result.get("followup_question", ""),
                        "reasoning": followup_result.get("reasoning", "")
                    }
                    state["follow_up_depth"] += 1
                else:
                    # Reset follow-up depth when no follow-up needed
                    state["follow_up_depth"] = 0

            # Add user message to conversation
            if state["current_message"]:
                state = add_message_to_state(state, "user", state["current_message"])

            # Generate assistant response (ask next question)
            response, quick_replies = self._generate_next_question(state)

            # Update state with response
            state["assistant_response"] = response
            state["quick_replies"] = quick_replies

            # Add assistant message to conversation
            state = add_message_to_state(state, "assistant", response)

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

    def _generate_next_question(self, state: TaxConsultationState) -> Tuple[str, List[str]]:
        """
        Generate next question to ask
        Phase 3: Adds clarification mode, explanation generation, and adaptive follow-ups
        """

        # Phase 3: Check if we're in clarification mode (or adaptive follow-up, or verification)
        if state.get("clarification_mode", False) and state.get("clarification_context"):
            context = state["clarification_context"]
            context_type = context.get("type", "clarification")

            if context_type == "verification":
                # Verification question for low/medium confidence tag
                verification_q = context.get("clarification_question", "")
                if verification_q:
                    # Exit clarification mode after asking
                    state["clarification_mode"] = False
                    return verification_q, ["Yes, that's correct", "No, that's not right", "Let me clarify"]
            elif context_type == "adaptive_followup":
                # Adaptive follow-up question
                followup_q = context.get("followup_question", "")
                if followup_q:
                    # Exit clarification mode after asking
                    state["clarification_mode"] = False
                    return followup_q, ["Yes", "No", "Please explain"]
            else:
                # Regular clarification question
                clarification_q = context.get("clarification_question", "")
                if clarification_q:
                    # Exit clarification mode after asking
                    state["clarification_mode"] = False
                    return clarification_q, ["Yes", "No", "I'm not sure"]

        # Determine the next question to ask
        next_question = self._select_next_question(state)

        if not next_question:
            # No more questions - should transition to forms analysis
            state["should_transition"] = True
            return "Thank you for providing all that information. Let me analyze your tax situation and determine the forms you'll need.", []

        # Mark this question as asked
        question_id = next_question.get("id")
        if question_id and question_id not in state["asked_question_ids"]:
            state["asked_question_ids"].append(question_id)

        # Get the question text and quick replies
        question_text = next_question.get("question", "")
        quick_replies = next_question.get("quick_replies", ["Yes", "No"])

        # Phase 3: Add explanation if enabled
        if science_config.USE_EXPLANATION_GENERATION and len(state["messages"]) > 2:
            explanation = self._generate_question_explanation(
                question_text,
                state
            )
            if explanation:
                # Prepend explanation to question
                question_text = f"{explanation}\n\n{question_text}"

        return question_text, quick_replies

    def _generate_intake_response(self, state: TaxConsultationState) -> Tuple[str, List[str], List[str]]:
        """
        DEPRECATED: Legacy method for backward compatibility
        Use _generate_next_question instead
        """

        # This method is kept for any external callers, but internally we use the new flow
        question_text, quick_replies = self._generate_next_question(state)
        return question_text, quick_replies, []  # Tags now handled separately

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
        """
        Check if we should transition to forms analysis
        Phase 3: Adds verification phase for low/medium confidence tags
        """

        min_tags_threshold = science_config.MIN_TAGS_FOR_TRANSITION
        conversation_length = len(state["messages"])

        has_sufficient_tags = len(state["assigned_tags"]) >= min_tags_threshold
        has_sufficient_conversation = conversation_length >= science_config.MIN_CONVERSATION_LENGTH

        # Phase 3: Check if we need verification phase
        if science_config.USE_VERIFICATION_PHASE and has_sufficient_tags and has_sufficient_conversation:
            # Check for unverified low/medium confidence tags
            unverified_tags = []
            for tag in state["assigned_tags"]:
                confidence = state["tag_confidence"].get(tag, "high")
                if confidence in ["low", "medium"]:
                    # Check if already verified
                    already_verified = any(
                        v.get("tag") == tag and v.get("verified", False)
                        for v in state.get("verification_needed", [])
                    )
                    if not already_verified:
                        unverified_tags.append({
                            "tag": tag,
                            "confidence": confidence,
                            "reasoning": state["tag_assignment_reasoning"].get(tag, {}).get("reasoning", "")
                        })

            # If there are unverified tags, enter verification mode
            if unverified_tags and not state.get("clarification_mode", False):
                # Set up verification for first unverified tag
                first_unverified = unverified_tags[0]
                state["clarification_mode"] = True
                state["clarification_context"] = {
                    "type": "verification",
                    "tag": first_unverified["tag"],
                    "confidence": first_unverified["confidence"],
                    "clarification_question": self._generate_verification_question(
                        first_unverified["tag"],
                        first_unverified["confidence"],
                        state
                    )
                }
                # Don't transition yet
                return state

        # Only transition with sufficient information - never force transition in initial conversations
        if has_sufficient_tags and has_sufficient_conversation:
            state["should_transition"] = True
            state["transition_reason"] = "Sufficient information gathered for forms analysis"
            state["current_phase"] = "forms_analysis"

        return state

    def _select_next_question_with_llm(self, state: TaxConsultationState) -> Optional[Dict[str, Any]]:
        """
        Use LLM to intelligently select the most relevant next question

        This is the Phase 2 intelligent question selection
        """

        # Get available questions
        available_questions = self._get_available_questions(state)

        if not available_questions:
            return None

        # Get conversation context
        conversation_context = get_conversation_context(state, last_n=15)

        # Build state summary
        current_state_summary = {
            "assigned_tags": state.get("assigned_tags", []),
            "completed_modules": state.get("completed_modules", []),
            "current_module": state.get("current_module"),
            "conversation_turns": len(state.get("messages", [])) // 2
        }

        # Build prompt
        prompt = build_question_selection_prompt(
            conversation_context=conversation_context,
            current_state=current_state_summary,
            available_questions=available_questions
        )

        # Call LLM
        from langchain_core.messages import HumanMessage
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))

                # Check if ready for transition
                if result.get("ready_for_transition", False):
                    state["should_transition"] = True
                    state["transition_reason"] = result.get("transition_reason", "LLM determined sufficient information gathered")
                    return None

                # Get selected question ID
                selected_id = result.get("selected_question_id")
                if selected_id:
                    # Find the question object
                    for q in available_questions:
                        if q.get("id") == selected_id:
                            # Mark skipped questions
                            skip_ids = result.get("skip_questions", [])
                            for skip_id in skip_ids:
                                if skip_id not in state["skipped_question_ids"]:
                                    state["skipped_question_ids"].append(skip_id)

                            return q

        except Exception as e:
            print(f"LLM question selection error: {e}")
            # Fallback to deterministic selection
            return self._select_next_question_deterministic(state)

        # If LLM failed, use fallback
        return self._select_next_question_deterministic(state)

    def _get_available_questions(self, state: TaxConsultationState) -> List[Dict[str, Any]]:
        """Get all questions that haven't been asked or skipped yet"""

        asked_ids = set(state.get("asked_question_ids", []))
        skipped_ids = set(state.get("skipped_question_ids", []))

        available = []

        # Gating questions
        gating_questions = state.get("available_gating_questions", [])
        for q in gating_questions:
            qid = q.get("id")
            if qid and qid not in asked_ids and qid not in skipped_ids:
                available.append(q)

        # Module questions
        modules = self.knowledge_base.get("intake", {}).get("modules", {})
        for module_id, module_data in modules.items():
            module_questions = module_data.get("questions", [])
            for q in module_questions:
                qid = q.get("id")
                if qid and qid not in asked_ids and qid not in skipped_ids:
                    available.append(q)

        return available

    def _select_next_question(self, state: TaxConsultationState) -> Optional[Dict[str, Any]]:
        """
        Select the next question to ask

        Uses LLM-based or deterministic selection based on config flag
        """

        # Use LLM-based selection if enabled
        if science_config.USE_LLM_QUESTION_SELECTION:
            return self._select_next_question_with_llm(state)
        else:
            return self._select_next_question_deterministic(state)

    def _select_next_question_deterministic(self, state: TaxConsultationState) -> Optional[Dict[str, Any]]:
        """
        Deterministic question selection (original logic)

        Select based on:
        1. Current module (if in a module)
        2. Gating questions (if still in gating phase)
        3. Previously asked questions
        """

        # If no current module, ask gating questions
        if not state["current_module"]:
            return self._select_next_gating_question(state)

        # If in a module, ask module questions
        return self._select_next_module_question(state)

    def _select_next_gating_question(self, state: TaxConsultationState) -> Optional[Dict[str, Any]]:
        """Select next gating question that hasn't been asked"""

        gating_questions = state["available_gating_questions"]
        asked_ids = state["asked_question_ids"]

        # Find first unasked gating question
        for question in gating_questions:
            question_id = question.get("id")
            if question_id and question_id not in asked_ids:
                # Check if we should skip this question based on context
                if not self._should_skip_question(question, state):
                    return question
                else:
                    # Mark as skipped
                    if question_id not in state["skipped_question_ids"]:
                        state["skipped_question_ids"].append(question_id)

        # All gating questions have been asked/skipped
        # Now check if we should enter any modules based on yes responses
        triggered_module = self._get_triggered_module(state)
        if triggered_module:
            state["current_module"] = triggered_module
            return self._select_next_module_question(state)

        # No modules to enter - all done with intake
        return None

    def _select_next_module_question(self, state: TaxConsultationState) -> Optional[Dict[str, Any]]:
        """Select next module question that hasn't been asked"""

        current_module = state["current_module"]
        if not current_module:
            return None

        modules = self.knowledge_base.get("intake", {}).get("modules", {})
        if current_module not in modules:
            return None

        module_questions = modules[current_module].get("questions", [])
        asked_ids = state["asked_question_ids"]

        # Find first unasked module question
        for question in module_questions:
            question_id = question.get("id")
            if question_id and question_id not in asked_ids:
                # Check if we should skip this question based on context
                if not self._should_skip_question(question, state):
                    return question
                else:
                    # Mark as skipped
                    if question_id not in state["skipped_question_ids"]:
                        state["skipped_question_ids"].append(question_id)

        # All questions in this module have been asked/skipped
        # Mark module as completed and look for next module
        if current_module not in state["completed_modules"]:
            state["completed_modules"].append(current_module)

        # Reset current module and check if there are more modules to explore
        state["current_module"] = None
        next_module = self._get_next_triggered_module(state)
        if next_module:
            state["current_module"] = next_module
            return self._select_next_module_question(state)

        # No more questions
        return None

    def _should_skip_question(self, question: Dict[str, Any], state: TaxConsultationState) -> bool:
        """
        Determine if a question should be skipped based on previous responses
        Uses simple heuristics to avoid redundant questions
        """

        question_text = question.get("question", "").lower()
        question_id = question.get("id", "")

        # Get conversation history
        conversation_text = " ".join([
            msg["content"].lower()
            for msg in state["messages"]
            if msg["role"] == "user"
        ])

        # Skip rules based on question patterns

        # If user already said they're not a U.S. person, skip U.S.-person-only questions
        if "u.s. person" in question_text or "u.s. citizen" in question_text:
            if any(indicator in conversation_text for indicator in ["not a u.s.", "canadian citizen only", "no u.s. status"]):
                return True

        # If user said no employment income, skip employment questions
        if "employment" in question_text or "work" in question_text:
            if any(indicator in conversation_text for indicator in ["no employment", "not working", "retired"]):
                return True

        # If user said no business, skip business questions
        if "business" in question_text or "corporation" in question_text:
            if any(indicator in conversation_text for indicator in ["no business", "not self-employed"]):
                return True

        # If user said no real estate, skip real estate questions
        if "real estate" in question_text or "property" in question_text:
            if any(indicator in conversation_text for indicator in ["no property", "don't own"]):
                return True

        # Don't skip by default
        return False

    def _get_triggered_module(self, state: TaxConsultationState) -> Optional[str]:
        """
        Determine which module should be activated based on gating question responses

        Now uses dynamically built mapping from knowledge base instead of hardcoded dict
        Phase 3: Also checks skipped_modules list
        """

        # Build a mapping of which questions got "yes" responses
        # We need to match questions to their responses chronologically
        messages = state["messages"]
        asked_ids = state["asked_question_ids"]

        # Create pairs of (question_id, user_response)
        question_response_pairs = []
        for i in range(len(messages) - 1):
            if messages[i]["role"] == "assistant" and messages[i+1]["role"] == "user":
                # Try to find which question this was
                if i // 2 < len(asked_ids):
                    question_id = asked_ids[i // 2]
                    user_response = messages[i+1]["content"].lower()
                    question_response_pairs.append((question_id, user_response))

        # Check which gating questions got affirmative responses
        affirmative_indicators = ["yes", "yeah", "correct", "that's right", "yep", "sure"]

        for question_id, user_response in question_response_pairs:
            # Use dynamically built mapping
            if question_id in self.gating_to_module_map:
                is_affirmative = any(indicator in user_response for indicator in affirmative_indicators)
                if is_affirmative:
                    module = self.gating_to_module_map[question_id]
                    # Phase 3: Check if module is skipped
                    if module not in state["completed_modules"] and module not in state["skipped_modules"]:
                        return module

        return None

    def _get_next_triggered_module(self, state: TaxConsultationState) -> Optional[str]:
        """Get the next module that should be activated"""

        # Similar logic to _get_triggered_module but excludes completed modules
        return self._get_triggered_module(state)

    def _analyze_response_with_llm(
        self,
        user_response: str,
        previous_question: Dict[str, Any],
        state: TaxConsultationState
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze user's response and assign tags with confidence

        Returns dict with:
        - assigned_tags: List[str]
        - confidence: Dict[str, str] (tag -> high/medium/low)
        - reasoning: str
        - needs_clarification: bool
        """

        # Get conversation context
        conversation_context = get_conversation_context(state, last_n=10)

        # Build prompt
        prompt = build_tag_analysis_prompt(
            question_context=previous_question,
            user_response=user_response,
            conversation_history=conversation_context
        )

        # Call LLM
        from langchain_core.messages import HumanMessage
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))

                # Validate assigned tags exist in question action
                action = previous_question.get("action", "")
                possible_tags = re.findall(r'`([^`]+)`', action)

                # Filter to only tags mentioned in the question
                validated_tags = [
                    tag for tag in result.get("assigned_tags", [])
                    if tag in possible_tags or not possible_tags  # Allow if no tags specified
                ]

                return {
                    "assigned_tags": validated_tags,
                    "confidence": result.get("confidence", {}),
                    "reasoning": result.get("reasoning", ""),
                    "needs_clarification": result.get("needs_clarification", False),
                    "clarification_question": result.get("clarification_question", "")
                }

        except Exception as e:
            print(f"LLM tag analysis error: {e}")
            # Fallback to keyword-based approach
            return self._analyze_response_for_tags_fallback(user_response, previous_question, state)

        # If parsing failed, use fallback
        return self._analyze_response_for_tags_fallback(user_response, previous_question, state)

    def _analyze_response_for_tags_fallback(
        self,
        user_response: str,
        previous_question: Dict[str, Any],
        state: TaxConsultationState
    ) -> Dict[str, Any]:
        """
        Fallback keyword-based tag assignment (original logic)
        Used when LLM fails or as backup
        """

        # Check if user gave an affirmative response
        user_response_lower = user_response.lower()
        affirmative_indicators = ["yes", "yeah", "correct", "that's right", "yep", "sure", "definitely"]

        is_affirmative = any(indicator in user_response_lower for indicator in affirmative_indicators)

        if not is_affirmative:
            return {
                "assigned_tags": [],
                "confidence": {},
                "reasoning": "Response was not affirmative",
                "needs_clarification": False,
                "clarification_question": ""
            }

        # Extract tag from action
        action = previous_question.get("action", "")
        if "add tag" in action.lower():
            # Extract tag name from action like "Add tag `tag_name`"
            tag_match = re.search(r'`([^`]+)`', action)
            if tag_match:
                tag = tag_match.group(1)
                if tag not in state["assigned_tags"]:
                    return {
                        "assigned_tags": [tag],
                        "confidence": {tag: "high"},
                        "reasoning": "Affirmative keyword match",
                        "needs_clarification": False,
                        "clarification_question": ""
                    }

        return {
            "assigned_tags": [],
            "confidence": {},
            "reasoning": "No tags to assign",
            "needs_clarification": False,
            "clarification_question": ""
        }

    def _analyze_response_for_tags(
        self,
        user_response: str,
        previous_question_id: Optional[str],
        state: TaxConsultationState
    ) -> List[str]:
        """
        DEPRECATED: Legacy method for backward compatibility
        Use _analyze_response_with_llm instead
        """

        if not previous_question_id:
            return []

        # Find the question that was asked
        all_questions = state["available_gating_questions"].copy()

        # Add module questions
        modules = self.knowledge_base.get("intake", {}).get("modules", {})
        for module_data in modules.values():
            all_questions.extend(module_data.get("questions", []))

        # Find the previous question
        previous_question = None
        for q in all_questions:
            if q.get("id") == previous_question_id:
                previous_question = q
                break

        if not previous_question:
            return []

        # Use new LLM-based method
        result = self._analyze_response_with_llm(user_response, previous_question, state)
        return result.get("assigned_tags", [])

    def _extract_all_facts_from_response(self, user_response: str, state: TaxConsultationState) -> Dict[str, Any]:
        """
        Phase 3: Extract ALL tax-relevant facts from a user response

        This goes beyond the current question and looks for any mentioned facts
        that could assign tags from anywhere in the knowledge base
        """

        if not science_config.USE_MULTI_FACT_EXTRACTION:
            return {"extracted_facts": [], "inferred_facts": []}

        # Get all possible tags with descriptions
        tag_definitions = self.knowledge_base.get("tags", {}).get("tag_definitions", {})
        all_possible_tags = []
        for tag_id, tag_info in tag_definitions.items():
            all_possible_tags.append({
                "tag_id": tag_id,
                "description": tag_info.get("description", "")
            })

        # Get conversation history
        conversation_history = get_conversation_context(state, last_n=10)

        # Build prompt
        prompt = build_multi_fact_extraction_prompt(
            user_response=user_response,
            conversation_history=conversation_history,
            all_possible_tags=all_possible_tags
        )

        # Call LLM
        from langchain_core.messages import HumanMessage
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result

        except Exception as e:
            print(f"Multi-fact extraction error: {e}")

        return {"extracted_facts": [], "inferred_facts": []}

    def _apply_extracted_facts(self, extraction_result: Dict[str, Any], state: TaxConsultationState):
        """
        Apply the facts extracted from multi-fact extraction to state

        This assigns tags found in the user's response even if not directly asked
        """
        from datetime import datetime

        # Process explicit facts (high confidence)
        for fact in extraction_result.get("extracted_facts", []):
            tags = fact.get("related_tags", [])
            confidence = fact.get("confidence", "medium")
            evidence = fact.get("evidence", "")

            for tag in tags:
                if tag not in state["assigned_tags"]:
                    state["assigned_tags"].append(tag)
                    state["tag_confidence"][tag] = confidence
                    state["tag_assignment_reasoning"][tag] = {
                        "method": "multi_fact_extraction",
                        "fact": fact.get("fact", ""),
                        "evidence": evidence,
                        "confidence": confidence,
                        "timestamp": datetime.now().isoformat()
                    }

                    # Store in extracted facts for audit
                    state["extracted_facts"].append(fact)

        # Process inferred facts (lower confidence)
        for fact in extraction_result.get("inferred_facts", []):
            tags = fact.get("related_tags", [])
            confidence = fact.get("confidence", "low")
            evidence = fact.get("evidence", "")

            for tag in tags:
                if tag not in state["assigned_tags"]:
                    # For inferred facts, only add to verification_needed
                    # Don't assign immediately unless high confidence
                    if confidence == "high":
                        state["assigned_tags"].append(tag)
                        state["tag_confidence"][tag] = confidence
                        state["tag_assignment_reasoning"][tag] = {
                            "method": "multi_fact_inference",
                            "fact": fact.get("fact", ""),
                            "evidence": evidence,
                            "confidence": confidence,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        # Add to verification list
                        state["verification_needed"].append({
                            "tag": tag,
                            "fact": fact.get("fact", ""),
                            "confidence": confidence,
                            "evidence": evidence,
                            "added_at": datetime.now().isoformat()
                        })

    def _analyze_module_relevance(self, state: TaxConsultationState) -> Dict[str, Any]:
        """
        Phase 3: Smart Module Skipping

        Analyze which modules are relevant, can be skipped, or need verification
        based on the conversation so far
        """

        if not science_config.USE_SMART_MODULE_SKIPPING:
            return {"relevant_modules": [], "skip_modules": [], "verify_modules": []}

        # Get conversation summary
        conversation_context = get_conversation_context(state, last_n=10)
        initial_response = state["messages"][0]["content"] if state["messages"] else ""

        # Get all available modules
        modules = self.knowledge_base.get("intake", {}).get("modules", {})
        modules_info = []

        for module_id, module_data in modules.items():
            modules_info.append({
                "id": module_id,
                "name": module_data.get("name", ""),
                "description": module_data.get("description", "Module questions")
            })

        # Build prompt
        prompt = build_module_relevance_prompt(
            initial_response=initial_response,
            conversation_summary=conversation_context,
            modules=modules_info
        )

        # Call LLM
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result

        except Exception as e:
            print(f"Module relevance analysis error: {e}")

        # Fallback: all modules relevant
        return {"relevant_modules": [], "skip_modules": [], "verify_modules": []}

    def _apply_module_skipping(self, state: TaxConsultationState, relevance_result: Dict[str, Any]) -> TaxConsultationState:
        """
        Apply module skipping decisions to state
        """

        # Add modules to skip list
        skip_modules = relevance_result.get("skip_modules", [])
        for module_info in skip_modules:
            module_id = module_info.get("module_id")
            reasoning = module_info.get("reasoning", "")

            if module_id and module_id not in state["skipped_modules"]:
                state["skipped_modules"].append(module_id)

                # Log the decision
                print(f"[SMART SKIP] Skipping module {module_id}: {reasoning}")

        return state

    def _generate_question_explanation(self, question: str, state: TaxConsultationState) -> Optional[str]:
        """
        Phase 3: Explanation Generation

        Generate a brief explanation of why this question is relevant
        """

        if not science_config.USE_EXPLANATION_GENERATION:
            return None

        # Get conversation context
        conversation_context = get_conversation_context(state, last_n=10)
        assigned_tags = state["assigned_tags"]

        # Build prompt
        prompt = build_explanation_prompt(
            question=question,
            conversation_context=conversation_context,
            assigned_tags=assigned_tags
        )

        # Call LLM
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result.get("combined", "")

        except Exception as e:
            print(f"Explanation generation error: {e}")

        return None

    def _check_for_followup(
        self,
        original_question: Dict[str, Any],
        user_response: str,
        assigned_tags: List[str],
        state: TaxConsultationState
    ) -> Dict[str, Any]:
        """
        Phase 3: Adaptive Follow-Up Questions

        Determine if a follow-up question would be valuable
        """

        if not science_config.USE_ADAPTIVE_FOLLOWUPS:
            return {"needs_followup": False}

        # Build prompt
        original_q_text = original_question.get("question", "")
        tag_assigned = assigned_tags[0] if assigned_tags else "none"

        prompt = build_follow_up_question_prompt(
            original_question=original_q_text,
            user_response=user_response,
            tag_assigned=tag_assigned
        )

        # Call LLM
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result

        except Exception as e:
            print(f"Follow-up check error: {e}")

        return {"needs_followup": False}

    def _generate_verification_question(self, tag: str, confidence: str, state: TaxConsultationState) -> str:
        """
        Phase 3: Verification Phase

        Generate verification question for low/medium confidence tag
        """

        # Get tag definition
        tag_definitions = self.knowledge_base.get("tags", {}).get("tag_definitions", {})
        tag_info = tag_definitions.get(tag, {})
        tag_description = tag_info.get("description", "")

        # Get assignment reasoning
        reasoning = state["tag_assignment_reasoning"].get(tag, {})
        user_response = reasoning.get("user_response", "")

        # Simple verification question generator
        verification_text = f"Based on what you've told me, it seems you might have {tag_description.lower() if tag_description else 'this situation'}. Can you confirm if this is correct?"

        return verification_text

    def _detect_correction(self, message: str) -> bool:
        """
        Phase 3: Context Correction

        Detect if user is trying to correct a previous answer
        """

        correction_keywords = [
            "actually", "wait", "i meant", "correction", "i misspoke",
            "that's wrong", "not correct", "let me correct", "i was wrong",
            "i made a mistake", "change that", "i said earlier but"
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in correction_keywords)

    def _handle_correction(self, message: str, state: TaxConsultationState) -> TaxConsultationState:
        """
        Phase 3: Context Correction

        Handle user correction - analyze what they're correcting and update state
        """

        from datetime import datetime

        # Log the correction
        correction_entry = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "conversation_turn": len(state["messages"])
        }

        # Use LLM to understand what's being corrected
        conversation_context = get_conversation_context(state, last_n=10)

        # Simple prompt to understand correction
        prompt = f"""The user is making a correction to a previous statement in a tax consultation.

CONVERSATION HISTORY:
{conversation_context}

CORRECTION MESSAGE:
{message}

CURRENT ASSIGNED TAGS:
{', '.join(state['assigned_tags']) if state['assigned_tags'] else 'None'}

Analyze what the user is correcting and respond in JSON format:
{{
    "corrected_fact": "What fact is being corrected",
    "tags_to_remove": ["tag1", "tag2"],
    "tags_to_add": ["tag3"],
    "confidence": "high/medium/low",
    "reasoning": "Brief explanation"
}}
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))

                # Remove tags
                for tag in result.get("tags_to_remove", []):
                    if tag in state["assigned_tags"]:
                        state["assigned_tags"].remove(tag)
                        # Update confidence to mark as removed
                        if tag in state["tag_confidence"]:
                            del state["tag_confidence"][tag]

                correction_entry["tags_removed"] = result.get("tags_to_remove", [])
                correction_entry["tags_added"] = result.get("tags_to_add", [])
                correction_entry["reasoning"] = result.get("reasoning", "")

                # Add tags
                for tag in result.get("tags_to_add", []):
                    if tag not in state["assigned_tags"]:
                        state["assigned_tags"].append(tag)
                        state["tag_confidence"][tag] = result.get("confidence", "high")
                        state["tag_assignment_reasoning"][tag] = {
                            "method": "user_correction",
                            "user_response": message,
                            "confidence": result.get("confidence", "high"),
                            "reasoning": result.get("reasoning", ""),
                            "timestamp": datetime.now().isoformat()
                        }

        except Exception as e:
            print(f"Correction handling error: {e}")
            correction_entry["error"] = str(e)

        # Add to corrections log
        state["corrections_made"].append(correction_entry)

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

        # Build tag definitions text
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

        system_prompt = build_forms_analysis_system_prompt(tags_text)
        user_prompt = build_forms_analysis_user_prompt(tags)

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