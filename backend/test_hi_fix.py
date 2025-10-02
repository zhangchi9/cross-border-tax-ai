"""
Test: Verify that saying 'hi' doesn't skip the first question
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


async def test_hi():
    """Test that 'hi' doesn't cause question skipping"""

    print("="*80)
    print("TEST: User says 'hi' - Should NOT skip first question")
    print("="*80)

    workflow = TaxConsultationWorkflow()

    # User says "hi"
    result = await workflow.start_consultation("hi", session_id="test_hi")

    assistant_response = result.get('assistant_response', '')
    questions_asked = len(result.get('asked_question_ids', []))

    print(f"\nUser: hi")
    print(f"Assistant: {assistant_response}")
    print(f"\nQuestions asked: {questions_asked}")

    # Check if first question was asked
    expected_first_question = "Are you a U.S. citizen or U.S. green-card holder?"

    if expected_first_question in assistant_response:
        print(f"\n✅ SUCCESS: First question asked correctly!")
        print(f"   The system asks: '{expected_first_question}'")
        return True
    else:
        print(f"\n❌ FAIL: First question was NOT asked!")
        print(f"   Expected: '{expected_first_question}'")
        print(f"   Got: '{assistant_response}'")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_hi())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
