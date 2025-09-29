"""
Example usage of the Cross-Border Tax LLM-powered Agentic Framework
"""
import json
import asyncio
from llm_orchestrator import LLMCrossBorderTaxOrchestrator


async def example_consultation():
    """Example of a complete consultation session"""

    # Initialize the LLM orchestrator
    orchestrator = LLMCrossBorderTaxOrchestrator()

    print("=== Cross-Border Tax Consultation Example ===\n")

    # Start consultation
    print("Starting consultation...")
    response = await orchestrator.start_consultation(
        "I'm a U.S. citizen living in Canada with rental property in both countries"
    )

    session_id = response["session_id"]
    print(f"Session ID: {session_id}")
    print(f"Agent Response: {response['message']}\n")

    # Simulate client responses
    client_responses = [
        "Yes, I am a U.S. citizen",
        "Yes, I am a Canadian tax resident",
        "Yes, I own rental property in the U.S.",
        "Yes, I own rental property in Canada",
        "No, I don't have any business entities",
        "No, I don't have equity compensation"
    ]

    # Continue consultation
    for i, client_response in enumerate(client_responses):
        print(f"Client: {client_response}")

        response = await orchestrator.continue_consultation(session_id, client_response)

        print(f"Agent: {response['message']}")

        # Check if we've transitioned to forms analysis
        if response.get("transition"):
            print("\n=== TRANSITIONING TO FORMS ANALYSIS ===")
            forms_analysis = response.get("forms_analysis", {})

            print(f"\nAnalysis Summary: {forms_analysis.get('analysis_summary', 'N/A')}")

            print(f"\nComplexity: {forms_analysis.get('estimated_complexity', 'N/A')}")

            print("\nRequired Forms:")
            for form in forms_analysis.get("required_forms", []):
                print(f"  • {form['form']} ({form['jurisdiction']}) - Priority: {form['priority']}")
                print(f"    Due: {form['due_date']}")
                print(f"    Reason: {form['reason'][:100]}...")

            print("\nRecommendations:")
            for rec in forms_analysis.get("recommendations", []):
                print(f"  • {rec}")

            print("\nNext Steps:")
            for step in forms_analysis.get("next_steps", []):
                print(f"  • {step}")

            break

        print()

    # Example follow-up questions
    print("\n=== FOLLOW-UP QUESTIONS ===")

    follow_up_questions = [
        "What are the deadlines for these forms?",
        "Which forms should I prioritize?",
        "How much will this cost?"
    ]

    for question in follow_up_questions:
        print(f"\nClient: {question}")
        response = await orchestrator.continue_consultation(session_id, question)
        print(f"Agent: {response['message']}")

    # Get session summary
    print("\n=== SESSION SUMMARY ===")
    summary = orchestrator.get_session_summary(session_id)
    print(json.dumps(summary, indent=2))


async def example_simple_consultation():
    """Example of a simpler consultation"""

    orchestrator = LLMCrossBorderTaxOrchestrator()

    print("=== Simple Consultation Example ===\n")

    # Start with employment question
    response = await orchestrator.start_consultation(
        "I work remotely for a U.S. company while living in Canada"
    )

    session_id = response["session_id"]
    print(f"Agent: {response['message']}\n")

    # Quick responses
    responses = [
        "Yes, I'm a Canadian resident",
        "No, I'm not a U.S. citizen",
        "Yes, I work entirely from Canada"
    ]

    for client_response in responses:
        print(f"Client: {client_response}")
        response = await orchestrator.continue_consultation(session_id, client_response)
        print(f"Agent: {response['message']}\n")

        if response.get("transition"):
            forms = response.get("forms_analysis", {}).get("required_forms", [])
            print(f"Result: {len(forms)} forms identified")
            for form in forms:
                print(f"  • {form['form']} ({form['jurisdiction']})")
            break


async def main():
    """Main function to run examples"""
    # Run example consultation
    await example_consultation()

    print("\n" + "="*60 + "\n")

    # Run simple consultation
    await example_simple_consultation()


if __name__ == "__main__":
    asyncio.run(main())