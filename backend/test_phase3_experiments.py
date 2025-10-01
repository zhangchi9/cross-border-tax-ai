"""
Phase 3 Enhancement Testing - Standalone Experiment Script

This script tests all Phase 3 enhancements for the cross-border tax consultation workflow:
- Multi-fact extraction from complex responses
- Smart module skipping based on user situation
- Context correction handling
- Full conversation flow to forms analysis
- Feature flag comparison (Phase 2 vs Phase 3)
- Session state export

Usage:
    python test_phase3_experiments.py --test all
    python test_phase3_experiments.py --test 1
    python test_phase3_experiments.py --interactive
"""

import asyncio
import argparse
import json
from datetime import datetime
from typing import Dict, Any, List

from science.agents.workflow import TaxConsultationWorkflow
from science.config import science_config


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_separator(char="=", length=80):
    """Print a visual separator line"""
    print(char * length)


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "#" * 80)
    print(f"# {text}")
    print("#" * 80 + "\n")


def print_message(role: str, content: str, quick_replies: list = None):
    """Print a formatted conversation message"""
    print_separator()
    print(f"{role.upper()}:")
    print(content)
    if quick_replies:
        print(f"\nQuick Replies: {', '.join(quick_replies)}")
    print_separator()


def print_state_summary(state: dict):
    """Print a comprehensive state summary"""
    print("\n" + "=" * 80)
    print("STATE SUMMARY")
    print("=" * 80)

    # Basic info
    print(f"Phase: {state['current_phase']}")
    print(f"Current Module: {state.get('current_module', 'None')}")
    print(f"Conversation Turns: {len(state['messages'])}")
    print(f"Session ID: {state.get('session_id', 'N/A')}")

    # Tags
    print(f"\n[Tags] Assigned Tags ({len(state['assigned_tags'])}):")
    if state['assigned_tags']:
        for tag in state['assigned_tags']:
            confidence = state['tag_confidence'].get(tag, 'unknown')
            reasoning = state['tag_assignment_reasoning'].get(tag, {})
            method = reasoning.get('method', 'llm_analysis')
            print(f"  - {tag}")
            print(f"    Confidence: {confidence} | Method: {method}")
    else:
        print("  (none)")

    # Phase 3: Extracted facts
    if state.get('extracted_facts'):
        print(f"\n[Phase 3] Extracted Facts ({len(state['extracted_facts'])}):")
        for fact in state['extracted_facts'][-5:]:  # Last 5
            print(f"  - {fact.get('fact', 'N/A')}")
            print(f"    Confidence: {fact.get('confidence', 'N/A')}")
            print(f"    Evidence: {fact.get('evidence', 'N/A')[:60]}...")

    # Phase 3: Skipped modules
    if state.get('skipped_modules'):
        print(f"\n[Phase 3] Skipped Modules: {', '.join(state['skipped_modules'])}")

    # Phase 3: Corrections
    if state.get('corrections_made'):
        print(f"\n[Phase 3] Corrections Made: {len(state['corrections_made'])}")
        for corr in state['corrections_made']:
            print(f"  - Turn {corr.get('conversation_turn', 'N/A')}: {corr.get('reasoning', 'N/A')[:60]}...")

    # Phase 3: Verification
    if state.get('verification_needed'):
        print(f"\n[Phase 3] Tags Needing Verification: {len(state['verification_needed'])}")
        for v in state['verification_needed']:
            print(f"  - {v.get('tag', 'N/A')} ({v.get('confidence', 'N/A')})")

    # Module progress
    print(f"\n[Progress]")
    print(f"  Completed Modules: {', '.join(state.get('completed_modules', [])) or 'None'}")
    print(f"  Questions Asked: {len(state.get('asked_question_ids', []))}")
    print(f"  Questions Skipped: {len(state.get('skipped_question_ids', []))}")

    # Transition status
    print(f"\n[Transition]")
    print(f"  Ready to Transition: {state.get('should_transition', False)}")
    if state.get('transition_reason'):
        print(f"  Transition Reason: {state['transition_reason']}")

    print("=" * 80 + "\n")


def print_forms_analysis(state: dict):
    """Print forms analysis results"""
    print("\n" + "=" * 80)
    print("FORMS ANALYSIS RESULTS")
    print("=" * 80)

    print(f"\nComplexity: {state.get('estimated_complexity', 'N/A').upper()}")

    print(f"\n[Required Forms] ({len(state.get('required_forms', []))}):")
    for form in state.get('required_forms', []):
        print(f"\n  {form.get('form', 'N/A')} - {form.get('jurisdiction', 'N/A')}")
        print(f"    Priority: {form.get('priority', 'N/A')}")
        print(f"    Due: {form.get('due_date', 'N/A')}")
        print(f"    Description: {form.get('description', 'N/A')}")

    print(f"\n[Recommendations]:")
    for i, rec in enumerate(state.get('recommendations', []), 1):
        print(f"  {i}. {rec}")

    print(f"\n[Next Steps]:")
    for i, step in enumerate(state.get('next_steps', []), 1):
        print(f"  {i}. {step}")

    print("=" * 80 + "\n")


# ============================================================================
# TEST SCENARIOS
# ============================================================================

async def test_scenario_1_multifact():
    """Test Scenario 1: Multi-Fact Extraction

    Tests Phase 3 multi-fact extraction by providing a complex initial response
    with multiple tax situations embedded in a single message.
    """
    print_header("TEST SCENARIO 1: MULTI-FACT EXTRACTION")

    # Create workflow
    workflow = TaxConsultationWorkflow()
    session_id = "test_multifact_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    # Complex initial message with multiple facts
    initial_message = """Hi, I'm a US citizen who moved to Canada last year for a job at a tech company.
I still have my 401k account from my previous US employer, and I'm renting out a condo I own in Seattle.
I also opened an RRSP account here in Canada for retirement savings."""

    print("Testing multi-fact extraction from complex initial response...\n")
    print_message("user", initial_message)

    # Start consultation
    result = await workflow.start_consultation(initial_message, session_id=session_id)

    # Print response
    print_message(
        "assistant",
        result['assistant_response'],
        result.get('quick_replies', [])
    )

    # Print state
    print_state_summary(result)

    print("\n[EXPECTED BEHAVIOR]:")
    print("System should extract multiple facts from single response:")
    print("  - US citizenship -> us_person_worldwide_filing")
    print("  - Moved to Canada -> cross_border_residency, residency_change_dual_status")
    print("  - 401k -> cross_border_retirement_plans")
    print("  - Seattle rental -> us_person_us_rental")
    print("  - RRSP -> tfsa_resp_us_person (potentially)")
    print("\n[CHECK] Did system assign 4-5 tags from this single response?")
    print(f"[RESULT] Assigned {len(result['assigned_tags'])} tags")

    return result


async def test_scenario_2_smart_skipping():
    """Test Scenario 2: Smart Module Skipping

    Tests Phase 3 smart module skipping when user clearly indicates
    no business ownership (W-2 employment only).
    """
    print_header("TEST SCENARIO 2: SMART MODULE SKIPPING")

    # New workflow
    workflow = TaxConsultationWorkflow()
    session_id = "test_skip_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    # Clear message about W-2 employment only
    message1 = "I'm a W-2 employee at a Canadian company. No business ownership, just regular employment."
    print_message("user", message1)

    result = await workflow.start_consultation(message1, session_id=session_id)
    print_message("assistant", result['assistant_response'], result.get('quick_replies', []))
    print_state_summary(result)

    # Continue
    message2 = "Yes, I'm a Canadian resident"
    print_message("user", message2)

    result = await workflow.continue_consultation(session_id, message2)
    print_message("assistant", result['assistant_response'], result.get('quick_replies', []))
    print_state_summary(result)

    print("\n[EXPECTED BEHAVIOR]:")
    print("System should:")
    print("  - Detect 'W-2 employee' and 'No business ownership'")
    print("  - Mark 'business_entities' module as skipped")
    print("  - Never ask business-related questions")
    print("\n[CHECK] Is 'business_entities' in Skipped Modules list above?")
    skipped = result.get('skipped_modules', [])
    print(f"[RESULT] Skipped modules: {skipped}")

    return result


async def test_scenario_3_context_correction():
    """Test Scenario 3: Context Correction

    Tests Phase 3 correction handling when user corrects a previous answer.
    """
    print_header("TEST SCENARIO 3: CONTEXT CORRECTION")

    # New workflow
    workflow = TaxConsultationWorkflow()
    session_id = "test_correct_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initial conversation
    msg1 = "I'm a Canadian resident"
    print_message("user", msg1)
    result = await workflow.start_consultation(msg1, session_id=session_id)
    print_message("assistant", result['assistant_response'], result.get('quick_replies', []))

    msg2 = "No, I don't have any businesses"
    print_message("user", msg2)
    result = await workflow.continue_consultation(session_id, msg2)
    print_message("assistant", result['assistant_response'], result.get('quick_replies', []))

    print("\n... A few turns later ...\n")

    # Make a correction
    correction = """Actually, wait - I forgot to mention I do have a small LLC for freelance consulting work.
It's not very active, so I didn't think of it as a 'business' initially."""

    print_message("user", correction)
    result = await workflow.continue_consultation(session_id, correction)
    print_message("assistant", result['assistant_response'], result.get('quick_replies', []))
    print_state_summary(result)

    print("\n[EXPECTED BEHAVIOR]:")
    print("System should:")
    print("  - Detect correction keywords ('Actually, wait')")
    print("  - Add business-related tags (business_entity_foreign_ownership, etc.)")
    print("  - Re-enable business_entities module")
    print("  - Log correction in corrections_made[]")
    print("\n[CHECK] Are there entries in 'Corrections Made' section above?")
    corrections = result.get('corrections_made', [])
    print(f"[RESULT] Corrections made: {len(corrections)}")

    return result


async def test_scenario_4_full_conversation():
    """Test Scenario 4: Full Conversation Flow

    Tests complete conversation flow through to forms analysis phase.
    """
    print_header("TEST SCENARIO 4: FULL CONVERSATION FLOW")

    # New workflow
    workflow = TaxConsultationWorkflow()
    session_id = "test_full_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    # Conversation messages
    messages = [
        "I'm a US citizen living in Canada",
        "Yes, I moved here last year",
        "I work as a W-2 employee",
        "I have bank accounts in both countries",
        "Yes, I own a rental property in the US",
        "I have an RRSP in Canada",
        "No other investments",
    ]

    # Start
    print_message("user", messages[0])
    result = await workflow.start_consultation(messages[0], session_id=session_id)
    print_message("assistant", result['assistant_response'], result.get('quick_replies', []))
    print_state_summary(result)

    # Continue through conversation
    for i, msg in enumerate(messages[1:], 2):
        print(f"\n--- Turn {i} ---\n")
        print_message("user", msg)
        result = await workflow.continue_consultation(session_id, msg)
        print_message("assistant", result['assistant_response'], result.get('quick_replies', []))
        print_state_summary(result)

        # Check if transitioned
        if result['current_phase'] == 'forms_analysis':
            print("\n[SUCCESS] TRANSITIONED TO FORMS ANALYSIS!")
            print_forms_analysis(result)
            break

    # If not transitioned, force it
    if result['current_phase'] != 'forms_analysis':
        print("\n[INFO] Forcing transition to forms analysis...")
        result = await workflow.force_transition_to_forms_analysis(session_id)
        print_message("assistant", result['assistant_response'])
        print_forms_analysis(result)

    return result


async def test_scenario_5_feature_flags():
    """Test Scenario 5: Feature Flag Testing

    Compares behavior with Phase 3 features on vs off.
    """
    print_header("TEST SCENARIO 5: FEATURE FLAG TESTING (PHASE 2 vs PHASE 3)")

    # Save original config
    original_flags = {
        'multi_fact': science_config.USE_MULTI_FACT_EXTRACTION,
        'smart_skip': science_config.USE_SMART_MODULE_SKIPPING,
        'explanation': science_config.USE_EXPLANATION_GENERATION,
        'clarification': science_config.USE_AUTO_CLARIFICATION,
        'followups': science_config.USE_ADAPTIVE_FOLLOWUPS,
        'verification': science_config.USE_VERIFICATION_PHASE,
        'progressive': science_config.USE_PROGRESSIVE_ASSIGNMENT,
        'correction': science_config.USE_CONTEXT_CORRECTION,
    }

    # Test message
    test_msg = "I'm a US citizen living in Canada with rental property in Seattle and an RRSP account"

    print("Test Message:")
    print(f"  '{test_msg}'\n")

    # Test with Phase 3 ON
    print_separator("=", 80)
    print("PHASE 3 ENABLED")
    print_separator("=", 80)

    workflow_p3 = TaxConsultationWorkflow()
    session_p3 = "test_p3on_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    result_p3 = await workflow_p3.start_consultation(test_msg, session_id=session_p3)

    print(f"Tags assigned: {len(result_p3['assigned_tags'])}")
    print(f"Tags: {result_p3['assigned_tags']}")
    print(f"Extracted facts: {len(result_p3.get('extracted_facts', []))}")

    # Disable Phase 3
    science_config.USE_MULTI_FACT_EXTRACTION = False
    science_config.USE_SMART_MODULE_SKIPPING = False
    science_config.USE_EXPLANATION_GENERATION = False
    science_config.USE_AUTO_CLARIFICATION = False
    science_config.USE_ADAPTIVE_FOLLOWUPS = False
    science_config.USE_VERIFICATION_PHASE = False
    science_config.USE_PROGRESSIVE_ASSIGNMENT = False
    science_config.USE_CONTEXT_CORRECTION = False

    # Test with Phase 3 OFF
    print("\n" + "=" * 80)
    print("PHASE 3 DISABLED (Phase 2 only)")
    print("=" * 80 + "\n")

    workflow_p2 = TaxConsultationWorkflow()
    session_p2 = "test_p3off_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    result_p2 = await workflow_p2.start_consultation(test_msg, session_id=session_p2)

    print(f"Tags assigned: {len(result_p2['assigned_tags'])}")
    print(f"Tags: {result_p2['assigned_tags']}")
    print(f"Extracted facts: {len(result_p2.get('extracted_facts', []))}")

    # Comparison
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"Phase 3: {len(result_p3['assigned_tags'])} tags assigned")
    print(f"Phase 2: {len(result_p2['assigned_tags'])} tags assigned")
    print(f"Difference: {len(result_p3['assigned_tags']) - len(result_p2['assigned_tags']):+d} tags")
    print("\n[EXPECTED] Phase 3 multi-fact extraction should assign MORE tags from same response.")

    # Restore config
    science_config.USE_MULTI_FACT_EXTRACTION = original_flags['multi_fact']
    science_config.USE_SMART_MODULE_SKIPPING = original_flags['smart_skip']
    science_config.USE_EXPLANATION_GENERATION = original_flags['explanation']
    science_config.USE_AUTO_CLARIFICATION = original_flags['clarification']
    science_config.USE_ADAPTIVE_FOLLOWUPS = original_flags['followups']
    science_config.USE_VERIFICATION_PHASE = original_flags['verification']
    science_config.USE_PROGRESSIVE_ASSIGNMENT = original_flags['progressive']
    science_config.USE_CONTEXT_CORRECTION = original_flags['correction']

    print("\n[INFO] Configuration restored")

    return result_p3


async def test_scenario_6_session_export(workflow, session_id):
    """Test Scenario 6: Session Export

    Exports session data for debugging or analysis.
    """
    print_header("TEST SCENARIO 6: SESSION EXPORT")

    # Get state
    session_state = await workflow.get_session_state(session_id)

    if session_state:
        # Save to file
        output_file = f"session_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(session_state, f, indent=2, default=str)

        print(f"[SUCCESS] Session exported to: {output_file}")
        print(f"\nSession Info:")
        print(f"  Phase: {session_state['current_phase']}")
        print(f"  Messages: {len(session_state['messages'])}")
        print(f"  Tags: {len(session_state['assigned_tags'])}")
        print(f"  Forms: {len(session_state.get('required_forms', []))}")
    else:
        print(f"[ERROR] Session {session_id} not found")


async def test_scenario_7_interactive():
    """Test Scenario 7: Interactive Testing

    Allows interactive conversation with the workflow.
    """
    print_header("TEST SCENARIO 7: INTERACTIVE TESTING")

    # Create interactive workflow
    workflow = TaxConsultationWorkflow()
    session_id = "test_interactive_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Type your messages below.")
    print("Commands: 'quit' to exit, 'state' to see state summary, 'force' to force forms analysis\n")

    # Get initial message
    user_input = input("Your message: ")

    if user_input.lower() != 'quit':
        result = await workflow.start_consultation(user_input, session_id=session_id)
        print_message("assistant", result['assistant_response'], result.get('quick_replies', []))

        # Conversation loop
        while True:
            user_input = input("\nYour message: ")

            if user_input.lower() == 'quit':
                print("Ending session...")
                break

            if user_input.lower() == 'state':
                print_state_summary(result)
                continue

            if user_input.lower() == 'force':
                result = await workflow.force_transition_to_forms_analysis(session_id)
                print_message("assistant", result['assistant_response'])
                print_forms_analysis(result)
                break

            result = await workflow.continue_consultation(session_id, user_input)
            print_message("assistant", result['assistant_response'], result.get('quick_replies', []))

            if result['current_phase'] == 'forms_analysis':
                print("\n[SUCCESS] Conversation complete! Forms analysis generated.")
                print_forms_analysis(result)
                break


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def run_tests(test_numbers: List[int], interactive: bool, export_session: bool):
    """Run selected test scenarios"""

    print_separator("=", 80)
    print("PHASE 3 ENHANCEMENT TESTING")
    print_separator("=", 80)
    print(f"\nConfiguration:")
    print(f"  AI Provider: {science_config.AI_MODEL_PROVIDER}")
    print(f"  Model: {science_config.OPENAI_MODEL if science_config.AI_MODEL_PROVIDER == 'openai' else science_config.GEMINI_MODEL}")
    print(f"\nPhase 3 Features:")
    print(f"  Multi-Fact Extraction: {science_config.USE_MULTI_FACT_EXTRACTION}")
    print(f"  Smart Module Skipping: {science_config.USE_SMART_MODULE_SKIPPING}")
    print(f"  Explanation Generation: {science_config.USE_EXPLANATION_GENERATION}")
    print(f"  Auto-Clarification: {science_config.USE_AUTO_CLARIFICATION}")
    print(f"  Adaptive Follow-ups: {science_config.USE_ADAPTIVE_FOLLOWUPS}")
    print(f"  Verification Phase: {science_config.USE_VERIFICATION_PHASE}")
    print(f"  Progressive Assignment: {science_config.USE_PROGRESSIVE_ASSIGNMENT}")
    print(f"  Context Correction: {science_config.USE_CONTEXT_CORRECTION}")

    results = {}

    # Run selected tests
    if 1 in test_numbers:
        results['test1'] = await test_scenario_1_multifact()

    if 2 in test_numbers:
        results['test2'] = await test_scenario_2_smart_skipping()

    if 3 in test_numbers:
        results['test3'] = await test_scenario_3_context_correction()

    if 4 in test_numbers:
        results['test4'] = await test_scenario_4_full_conversation()

    if 5 in test_numbers:
        results['test5'] = await test_scenario_5_feature_flags()

    # Export session if requested and we have test 4 result
    if export_session and 'test4' in results:
        workflow = TaxConsultationWorkflow()
        await test_scenario_6_session_export(workflow, results['test4']['session_id'])

    # Interactive mode
    if interactive:
        await test_scenario_7_interactive()

    # Final summary
    print_header("TEST SUMMARY")
    print(f"Tests completed: {len(results)}")
    print(f"Session IDs generated: {[r['session_id'] for r in results.values()]}")
    print("\n" + "=" * 80)
    print("All tests completed successfully!")
    print("=" * 80)


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Phase 3 Enhancement Testing - Standalone Experiment Script"
    )
    parser.add_argument(
        '--test',
        type=str,
        default='all',
        help='Test number to run (1-5) or "all" (default: all)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run interactive testing mode'
    )
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export session data from test 4'
    )

    args = parser.parse_args()

    # Parse test numbers
    if args.test.lower() == 'all':
        test_numbers = [1, 2, 3, 4, 5]
    else:
        try:
            test_numbers = [int(args.test)]
            if not 1 <= test_numbers[0] <= 5:
                print("Error: Test number must be between 1 and 5")
                return
        except ValueError:
            print("Error: Invalid test number. Use 1-5 or 'all'")
            return

    # Run tests
    asyncio.run(run_tests(test_numbers, args.interactive, args.export))


if __name__ == "__main__":
    main()
