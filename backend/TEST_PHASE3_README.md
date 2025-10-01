# Phase 3 Testing Guide

## Quick Start

```bash
# Run all tests
python test_phase3_experiments.py --test all

# Run specific test
python test_phase3_experiments.py --test 1

# Interactive mode
python test_phase3_experiments.py --interactive

# Run test 4 and export session data
python test_phase3_experiments.py --test 4 --export
```

## Test Scenarios

### Test 1: Multi-Fact Extraction
Tests Phase 3's ability to extract multiple facts from a single complex response.

**What it tests:**
- US citizenship detection
- Cross-border residency
- Retirement accounts (401k, RRSP)
- Rental property ownership

**Expected:** 4-5 tags assigned from single message

```bash
python test_phase3_experiments.py --test 1
```

### Test 2: Smart Module Skipping
Tests Phase 3's ability to skip irrelevant modules based on user context.

**What it tests:**
- Detection of W-2 employment
- Business module skipping when "no business ownership" mentioned
- Intelligent conversation flow

**Expected:** `business_entities` module marked as skipped

```bash
python test_phase3_experiments.py --test 2
```

### Test 3: Context Correction
Tests Phase 3's ability to handle user corrections mid-conversation.

**What it tests:**
- Correction keyword detection ("Actually, wait...")
- Re-enabling previously skipped modules
- Adding missed tags retroactively
- Logging corrections

**Expected:** Correction logged, business tags added after initially saying "no business"

```bash
python test_phase3_experiments.py --test 3
```

### Test 4: Full Conversation Flow
Tests complete conversation through to forms analysis.

**What it tests:**
- Multi-turn conversation
- Tag accumulation over multiple responses
- Automatic transition to forms analysis
- Forms recommendation generation

**Expected:** Complete conversation with 2+ tags, transition to forms analysis

```bash
python test_phase3_experiments.py --test 4
```

### Test 5: Feature Flag Comparison
Compares Phase 2 vs Phase 3 behavior side-by-side.

**What it tests:**
- Phase 3 feature flags
- Tag assignment differences
- Fact extraction differences

**Expected:** Phase 3 assigns more tags than Phase 2 from same input

```bash
python test_phase3_experiments.py --test 5
```

### Test 6: Session Export
Exports session data for debugging (runs after Test 4).

**What it tests:**
- Session state retrieval
- JSON export functionality

**Expected:** `session_export_<timestamp>.json` file created

```bash
python test_phase3_experiments.py --test 4 --export
```

### Test 7: Interactive Mode
Run your own custom conversation.

**Commands:**
- Type messages to chat
- `state` - View current state summary
- `force` - Force transition to forms analysis
- `quit` - End session

```bash
python test_phase3_experiments.py --interactive
```

## Expected Output

Each test produces:
- **Conversation turns** with user/assistant messages
- **State summaries** showing tags, facts, modules, corrections
- **Expected behavior** description
- **Check results** comparing actual vs expected

## Troubleshooting

### ModuleNotFoundError
Set PYTHONPATH:
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%           # Windows CMD
```

### API Key Errors
Check `.env` file has:
```
OPENAI_API_KEY=your_key_here
# or
GEMINI_API_KEY=your_key_here
```

### Import Errors
```bash
pip install -r science/requirements.txt
```

## Configuration

Edit `science/config.py` to toggle features:

```python
# AI Model
AI_MODEL_PROVIDER: str = "openai"  # or "gemini"

# Phase 3 Features
USE_MULTI_FACT_EXTRACTION: bool = True
USE_SMART_MODULE_SKIPPING: bool = True
USE_EXPLANATION_GENERATION: bool = True
USE_AUTO_CLARIFICATION: bool = True
USE_ADAPTIVE_FOLLOWUPS: bool = True
USE_VERIFICATION_PHASE: bool = True
USE_PROGRESSIVE_ASSIGNMENT: bool = True
USE_CONTEXT_CORRECTION: bool = True
```

## Example Session

```bash
$ python test_phase3_experiments.py --test 1

================================================================================
PHASE 3 ENHANCEMENT TESTING
================================================================================

Configuration:
  AI Provider: openai
  Model: gpt-4o-mini

Phase 3 Features:
  Multi-Fact Extraction: True
  Smart Module Skipping: True
  ...

################################################################################
# TEST SCENARIO 1: MULTI-FACT EXTRACTION
################################################################################

Testing multi-fact extraction from complex initial response...

================================================================================
USER:
Hi, I'm a US citizen who moved to Canada last year for a job at a tech company.
I still have my 401k account from my previous US employer, and I'm renting out
a condo I own in Seattle. I also opened an RRSP account here in Canada for
retirement savings.
================================================================================

================================================================================
ASSISTANT:
Thank you for sharing that information...
================================================================================

================================================================================
STATE SUMMARY
================================================================================
Phase: intake
Current Module: None
Conversation Turns: 2
Session ID: test_multifact_20251001_143022

[Tags] Assigned Tags (4):
  - us_person_worldwide_filing
    Confidence: high | Method: llm_analysis
  - cross_border_residency
    Confidence: high | Method: llm_analysis
  ...

[EXPECTED BEHAVIOR]:
System should extract multiple facts from single response:
  - US citizenship -> us_person_worldwide_filing
  - Moved to Canada -> cross_border_residency, residency_change_dual_status
  - 401k -> cross_border_retirement_plans
  - Seattle rental -> us_person_us_rental
  - RRSP -> tfsa_resp_us_person (potentially)

[CHECK] Did system assign 4-5 tags from this single response?
[RESULT] Assigned 4 tags

================================================================================
All tests completed successfully!
================================================================================
```

## Notes

- Uses `asyncio.run()` (works in regular Python, not Jupyter)
- Generates timestamped session IDs for each test
- All state summaries show Phase 3 features in action
- Export files saved to `backend/session_export_<timestamp>.json`
