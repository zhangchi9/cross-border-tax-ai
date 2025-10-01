"""
Debug script to test question selection logic
"""

from science.agents.state import create_initial_state, add_message_to_state
from science.agents.nodes import IntakeNode

# Create a mock state
state = create_initial_state("test-session", "I'm a U.S. citizen")

# Load intake node
intake_node = IntakeNode()

# Populate available gating questions
state["available_gating_questions"] = intake_node.knowledge_base.get("intake", {}).get("gating_questions", {}).get("questions", [])

print("=== Available Gating Questions ===")
for q in state["available_gating_questions"]:
    print(f"- {q['id']}: {q['question'][:60]}...")

print(f"\nTotal gating questions: {len(state['available_gating_questions'])}")

# Test selecting first question
print("\n=== Selecting First Question ===")
next_q = intake_node._select_next_question(state)
if next_q:
    print(f"Selected: {next_q['id']}")
    print(f"Question: {next_q['question'][:80]}...")
else:
    print("No question selected!")

# Mark it as asked
state["asked_question_ids"].append(next_q["id"])

# Add mock conversation
state = add_message_to_state(state, "assistant", next_q["question"])
state = add_message_to_state(state, "user", "Yes")

print("\n=== After First Response (Yes) ===")
print(f"Asked IDs: {state['asked_question_ids']}")

# Try to trigger module
print("\n=== Checking Module Trigger ===")
triggered = intake_node._get_triggered_module(state)
print(f"Triggered module: {triggered}")

# Select next question
print("\n=== Selecting Second Question ===")
next_q = intake_node._select_next_question(state)
if next_q:
    print(f"Selected: {next_q['id']}")
    print(f"Question: {next_q['question'][:80]}...")
    print(f"Current module: {state.get('current_module')}")
else:
    print("No question selected!")
    print(f"Current module: {state.get('current_module')}")
    print(f"Completed modules: {state.get('completed_modules')}")