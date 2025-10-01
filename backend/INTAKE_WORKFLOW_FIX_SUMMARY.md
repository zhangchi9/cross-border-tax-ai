# Intake Workflow Fix Summary

## Problem Statement

The intake workflow was stopping prematurely after asking only gating questions and not continuing to ask all relevant questions from the tax team's knowledge base.

## Root Causes Identified

### 1. Knowledge Base Parser Issues (CRITICAL)
**File**: `science/services/knowledge_parser.py`

**Problem**: The parser was only extracting **1 gating question** and **1 question per module** instead of all questions.

**Root Cause**: The regex pattern used a greedy lookahead `(?=\n\n|\n###|$)` that was too restrictive and only matched when there were two consecutive newlines, causing it to match only the first question.

**Fix**:
- Changed from complex lookahead pattern to simpler, more reliable pattern
- Old pattern: `r'### (.*?)\n- \*\*ID\*\*: `([^`]+)`\n- \*\*Action\*\*: (.*?)(?:\n- \*\*Quick Replies\*\*: (.*))?(?=\n\n|\n###|$)'`
- New pattern: `r'### ([^\n]+)\n- \*\*ID\*\*: `([^`]+)`\n- \*\*Action\*\*: ([^\n]+)'`
- Added separate extraction for quick replies
- Applied same fix to both `_parse_gating_questions()` and `_parse_module_questions()`

**Result**:
- **Gating questions**: 1 → **18 questions** ✓
- **Module questions**: 1 per module → **45 total questions across 9 modules** ✓

### 2. Workflow Routing Issues
**File**: `science/agents/workflow.py`

**Problem**: The `should_continue_intake()` function was forcing a transition to forms_analysis after only 10 messages, preventing the workflow from asking all questions.

**Fix**:
- Removed the hard 10-message limit
- Increased maximum conversation length to 150 messages (accounting for 18 gating + ~45 module questions)
- Ensured transition only happens when:
  - Explicit `should_transition` flag is set, OR
  - Sufficient tags are assigned AND minimum conversation length is met

**Result**: Intake phase can now continue through all relevant questions without premature termination.

### 3. IntakeNode Question Selection Logic
**File**: `science/agents/nodes.py`

**Problem**: The IntakeNode was relying on LLM to select questions, which didn't properly track which questions had been asked or intelligently skip irrelevant questions.

**Fix**: Completely rewrote the question selection logic with:

#### A. Deterministic Question Selection
- Replaced LLM-based question selection with rule-based selection
- New method `_select_next_question()` deterministically picks the next unasked question
- Tracks asked questions in `state["asked_question_ids"]`
- Tracks skipped questions in `state["skipped_question_ids"]`

#### B. Intelligent Question Skipping
- New method `_should_skip_question()` uses heuristics to skip irrelevant questions
- Examples:
  - If user says "not a U.S. person", skip U.S.-person-only questions
  - If user says "no employment", skip employment questions
  - If user says "no business", skip business questions
  - If user says "no real estate", skip property questions

#### C. Module Triggering Logic
- New method `_get_triggered_module()` determines which module to enter based on gating question responses
- Maps gating question IDs to module IDs
- Analyzes conversation history to match questions with user responses
- Activates modules only when user gives affirmative responses

#### D. Tag Assignment Logic
- New method `_analyze_response_for_tags()` extracts tags from user responses
- Checks if previous question's action contains "Add tag `tag_name`"
- Assigns tag only when user gives affirmative response (yes, yeah, correct, sure, etc.)
- Prevents duplicate tag assignment

### 4. State Management
**File**: `science/agents/state.py`

**Enhancement**: Added new fields to track question progression:
- `asked_question_ids: List[str]` - Track which questions have been asked
- `skipped_question_ids: List[str]` - Track which questions were skipped due to context

## Workflow Flow (After Fixes)

```
1. START
   ↓
2. Ask Gating Questions (one at a time)
   - Question 1: "Are you a U.S. citizen?"
   - Question 2: "Are you a Canadian resident?"
   - ... (18 total gating questions)
   - Skip questions based on previous responses
   ↓
3. Determine Triggered Modules
   - Based on "yes" responses to gating questions
   - Example: Yes to "U.S. citizen" → trigger "residency_elections" module
   ↓
4. Ask Module Questions (one at a time)
   - Residency module questions (4 questions)
   - Employment module questions (10 questions)
   - ... (depends on which modules were triggered)
   - Assign tags based on affirmative responses
   ↓
5. Complete All Modules
   - Mark each module as completed
   - Move to next triggered module
   ↓
6. Transition to Forms Analysis
   - When all relevant questions have been asked/skipped
   - OR when sufficient tags are assigned AND minimum conversation length is met
```

## Key Design Principles

### 1. One Question at a Time
- Workflow asks exactly ONE question per turn
- No multiple questions in a single response
- User answers, then next question is asked

### 2. Gating Questions First
- All applicable gating questions are asked before entering any modules
- Gating questions route to modules but don't assign tags
- Example: "Are you a U.S. citizen?" → "Go to Module A — Residency & Elections"

### 3. Module Questions Assign Tags
- Module questions directly assign tags
- Example: "Did you meet the U.S. Substantial Presence Test?" → "Add tag `us_resident_substantial_presence`"
- Tags drive forms recommendation in forms_analysis phase

### 4. Intelligent Skipping
- Questions are skipped based on conversation context
- Prevents asking irrelevant questions
- Improves user experience by reducing burden

### 5. Module Progression
- Modules are entered based on gating question responses
- All questions in a module are asked before moving to next module
- Multiple modules can be triggered in a single consultation

## Test Results

### Before Fixes
```
Gating questions: 1
Module residency_elections: 1 questions
Module employment_states: 1 questions
... (1 question per module)
Total module questions: 9
```

Workflow stopped after 3-4 questions.

### After Fixes
```
Gating questions: 18
Module residency_elections: 4 questions
Module employment_states: 10 questions
Module business_entities: 5 questions
Module real_estate: 7 questions
Module investments_financial: 6 questions
Module pensions_savings: 4 questions
Module equity_compensation: 2 questions
Module estates_gifts_trusts: 3 questions
Module reporting_cleanup: 4 questions
Total module questions: 45
```

Workflow continues through all relevant questions based on user responses.

## Files Modified

1. `backend/science/services/knowledge_parser.py`
   - Fixed `_parse_gating_questions()` regex pattern
   - Fixed `_parse_module_questions()` regex pattern
   - Both methods now extract all questions correctly

2. `backend/science/agents/workflow.py`
   - Updated `should_continue_intake()` to allow longer conversations
   - Removed premature 10-message cutoff
   - Increased maximum to 150 messages

3. `backend/science/agents/nodes.py`
   - Rewrote `_generate_intake_response()` with deterministic question selection
   - Added `_select_next_question()`
   - Added `_select_next_gating_question()`
   - Added `_select_next_module_question()`
   - Added `_should_skip_question()`
   - Added `_get_triggered_module()`
   - Added `_get_next_triggered_module()`
   - Added `_analyze_response_for_tags()`

4. `backend/science/agents/state.py`
   - Added `asked_question_ids` field
   - Added `skipped_question_ids` field
   - Updated `create_initial_state()` to initialize new fields

5. `backend/science/knowledge_cache/intake/questions.json`
   - Auto-regenerated with all 18 gating questions + 45 module questions

## Verification

Run the parser to verify:
```bash
cd backend
python -c "from science.services.knowledge_parser import parse_knowledge_base; kb = parse_knowledge_base(); print('Gating questions:', len(kb['intake']['gating_questions']['questions'])); [print(f'Module {k}: {len(v[\"questions\"])} questions') for k,v in kb['intake']['modules'].items()]"
```

Expected output:
```
Gating questions: 18
Module residency_elections: 4 questions
Module employment_states: 10 questions
Module business_entities: 5 questions
Module real_estate: 7 questions
Module investments_financial: 6 questions
Module pensions_savings: 4 questions
Module equity_compensation: 2 questions
Module estates_gifts_trusts: 3 questions
Module reporting_cleanup: 4 questions
```

## Future Enhancements

1. **More Sophisticated Skipping Logic**
   - Use LLM to analyze conversation context
   - More intelligent determination of irrelevant questions
   - Machine learning-based skip prediction

2. **User Profile Building**
   - Extract structured information from responses
   - Build comprehensive user profile during intake
   - Use profile to further optimize question selection

3. **Adaptive Questioning**
   - Adjust question order based on user responses
   - Prioritize most relevant questions
   - Dynamic module activation

4. **Progress Indicators**
   - Show user how many questions remain
   - Display estimated time to completion
   - Module progress tracking

## Conclusion

The intake workflow has been comprehensively fixed to:
- ✓ Extract all questions from knowledge base (18 gating + 45 module questions)
- ✓ Continue asking questions beyond gating questions
- ✓ Intelligently skip irrelevant questions based on context
- ✓ Properly trigger modules based on user responses
- ✓ Assign tags correctly when users answer module questions affirmatively
- ✓ Maintain one-question-at-a-time strategy
- ✓ Prevent premature transition to forms analysis

The workflow now provides a comprehensive, intelligent tax consultation experience that gathers all necessary information before generating forms recommendations.