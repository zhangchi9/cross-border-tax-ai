"""
Test: Verify no repeated questions after disabling problematic Phase 3 features

Reproduces the user's conversation:
1. hi
2. no (to US citizen)
3. I am a PR in canada and I received RSU from US
4. yes
5. yes
6. No I am not. I am a non tax residence of us

Should NOT ask same question multiple times
"""
import asyncio
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from science.agents.workflow import TaxConsultationWorkflow
from science.config import science_config


async def test_no_repeated_questions():
    """Test that questions are not repeated"""

    print("=" * 80)
    print("TEST: No Repeated Questions")
    print("=" * 80)
    print(f"\nDisabled Features:")
    print(f"  USE_ADAPTIVE_FOLLOWUPS: {science_config.USE_ADAPTIVE_FOLLOWUPS}")
    print(f"  USE_AUTO_CLARIFICATION: {science_config.USE_AUTO_CLARIFICATION}")
    print(f"  USE_VERIFICATION_PHASE: {science_config.USE_VERIFICATION_PHASE}")
    print()

    workflow = TaxConsultationWorkflow()
    session_id = "test_no_repeat"

    # Reproduce the user's conversation
    conversation = [
        ("hi", None),
        ("no", "Are you a U.S. citizen"),
        ("I am a PR in canada and I received RSU from US", None),
        ("yes", None),
        ("yes", None),
        ("No I am not. I am a non tax residence of us", None)
    ]

    questions_asked = []
    questions_text = []
    result = None

    for i, (user_msg, expected_question_about) in enumerate(conversation, 1):
        print(f"\n{'=' * 80}")
        print(f"Turn {i}")
        print(f"{'=' * 80}")
        print(f"\nUser: {user_msg}")

        if i == 1:
            result = await workflow.start_consultation(user_msg, session_id=session_id)
        else:
            result = await workflow.continue_consultation(session_id, user_msg)

        assistant_response = result.get('assistant_response', '')
        current_questions_asked = result.get('asked_question_ids', [])

        # Normalize question for comparison (remove explanations)
        question_normalized = assistant_response.split('\n\n')[-1] if '\n\n' in assistant_response else assistant_response
        question_normalized = question_normalized.strip()[:100]  # First 100 chars

        print(f"\nAssistant: {question_normalized}...")

        # Check for expected question if specified
        if expected_question_about and expected_question_about not in assistant_response:
            print(f"  ⚠️  Warning: Expected question about '{expected_question_about}' but didn't see it")

        # Track questions
        questions_text.append(question_normalized.lower())

        print(f"\nProgress:")
        print(f"  Tags: {len(result.get('assigned_tags', []))}")
        print(f"  Questions Asked IDs: {len(current_questions_asked)}")
        print(f"  Phase: {result.get('current_phase', 'unknown')}")

    # Check for repeated questions
    print(f"\n{'=' * 80}")
    print("CHECKING FOR REPEATED QUESTIONS")
    print(f"{'=' * 80}")

    repeated = []
    for i, q1 in enumerate(questions_text):
        for j, q2 in enumerate(questions_text):
            if i < j:  # Only check each pair once
                # Check if questions are very similar (simple check)
                # RSU obligation variations
                if ("rsu" in q1 and "obligat" in q1) and ("rsu" in q2 and "obligat" in q2):
                    repeated.append((i + 1, j + 1, "RSU obligations"))
                # US citizen variations
                elif ("u.s. citizen" in q1 or "u.s. green" in q1) and ("u.s. citizen" in q2 or "u.s. green" in q2):
                    repeated.append((i + 1, j + 1, "US citizen status"))

    if repeated:
        print(f"\n❌ FOUND REPEATED QUESTIONS:")
        for turn1, turn2, topic in repeated:
            print(f"  - Turn {turn1} and Turn {turn2}: Both ask about '{topic}'")
            print(f"    Turn {turn1}: {questions_text[turn1-1][:80]}...")
            print(f"    Turn {turn2}: {questions_text[turn2-1][:80]}...")
        return False
    else:
        print(f"\n✅ SUCCESS: No repeated questions detected!")
        print(f"  Asked {len(questions_text)} unique questions")
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_no_repeated_questions())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
