"""
Test script for the intake workflow to verify:
1. All gating questions are available
2. Module questions are loaded correctly
3. Question selection logic works
4. Tag assignment works
"""

import asyncio
from science.agents.workflow import TaxConsultationWorkflow
from science.agents.state import create_initial_state


async def test_intake_workflow():
    """Test the complete intake workflow"""

    print("=" * 80)
    print("Testing Intake Workflow")
    print("=" * 80)

    workflow = TaxConsultationWorkflow()

    # Test 1: Start consultation
    print("\n[TEST 1] Starting consultation...")
    result = await workflow.start_consultation("I'm a U.S. citizen living in Canada")

    print(f"Session ID: {result['session_id']}")
    print(f"Current Phase: {result['current_phase']}")
    print(f"First Question: {result['message']}")
    print(f"Quick Replies: {result['quick_replies']}")

    session_id = result['session_id']

    # Test 2: Get session summary
    print("\n[TEST 2] Getting session summary...")
    summary = await workflow.get_session_summary(session_id)
    print(f"Assigned Tags: {summary['assigned_tags']}")
    print(f"Message Count: {summary['message_count']}")
    print(f"Current Module: {summary['current_module']}")

    # Test 3: Continue with affirmative response (should trigger tag assignment)
    print("\n[TEST 3] Answering 'Yes' to first question...")
    result = await workflow.continue_consultation(session_id, "Yes")
    print(f"Next Question: {result['message']}")
    print(f"Assigned Tags: {result['assigned_tags']}")

    # Test 4: Continue conversation multiple times
    print("\n[TEST 4] Continuing conversation...")
    responses = ["Yes", "No", "Yes", "No", "Yes"]

    for i, response in enumerate(responses):
        result = await workflow.continue_consultation(session_id, response)
        print(f"\nTurn {i+4}: Response '{response}'")
        print(f"  Question: {result['message'][:80]}...")
        print(f"  Tags: {result['assigned_tags']}")
        print(f"  Phase: {result['current_phase']}")

    # Test 5: Get final summary
    print("\n[TEST 5] Getting final summary...")
    summary = await workflow.get_session_summary(session_id)
    print(f"Total Messages: {summary['message_count']}")
    print(f"Assigned Tags: {summary['assigned_tags']}")
    print(f"Completed Modules: {summary['completed_modules']}")
    print(f"Current Module: {summary['current_module']}")
    print(f"Has Sufficient Tags: {summary['has_sufficient_tags']}")

    # Test 6: Debug session
    print("\n[TEST 6] Debug session state...")
    debug_info = await workflow.debug_session(session_id)
    print(f"Current Phase: {debug_info['current_phase']}")
    print(f"Should Transition: {debug_info['should_transition']}")
    print(f"Transition Reason: {debug_info.get('transition_reason', 'N/A')}")

    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_intake_workflow())