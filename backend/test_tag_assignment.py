"""
Debug script to test tag assignment logic
"""

from science.agents.state import create_initial_state, add_message_to_state
from science.agents.nodes import IntakeNode

# Create a mock state
state = create_initial_state("test-session", "")

# Load intake node
intake_node = IntakeNode()

# Populate available gating questions
state["available_gating_questions"] = intake_node.knowledge_base.get("intake", {}).get("gating_questions", {}).get("questions", [])

# Simulate a conversation
print("=== Simulating Conversation ===\n")

# Question 1: us_person_check
q1 = state["available_gating_questions"][0]  # Should be us_person_check
state["asked_question_ids"].append(q1["id"])
state = add_message_to_state(state, "assistant", q1["question"])
state = add_message_to_state(state, "user", "Yes")

print(f"Q1 ID: {q1['id']}")
print(f"Q1 Action: {q1.get('action', 'N/A')}")
print(f"User response: Yes")

# Try to analyze the response
tags = intake_node._analyze_response_for_tags("Yes", q1["id"], state)
print(f"Tags extracted: {tags}")

# Check if tag is in action
import re
action = q1.get("action", "")
print(f"\nAction text: {action}")
if "add tag" in action.lower():
    print("Action contains 'add tag'")
    tag_match = re.search(r'`([^`]+)`', action)
    if tag_match:
        print(f"Tag match found: {tag_match.group(1)}")
    else:
        print("No tag match in action")
else:
    print("Action does NOT contain 'add tag'")

# Let's check a module question that should have a tag
print("\n\n=== Checking Module Question ===\n")
modules = intake_node.knowledge_base.get("intake", {}).get("modules", {})
residency_questions = modules["residency_elections"]["questions"]

q2 = residency_questions[0]  # Should be a1_substantial_presence
print(f"Module Q ID: {q2['id']}")
print(f"Module Q Action: {q2.get('action', 'N/A')}")

# Check if this has a tag
action = q2.get("action", "")
print(f"\nAction text: {action}")
if "add tag" in action.lower():
    print("Action contains 'add tag'")
    tag_match = re.search(r'`([^`]+)`', action)
    if tag_match:
        print(f"Tag match found: {tag_match.group(1)}")
else:
    print("Action does NOT contain 'add tag'")