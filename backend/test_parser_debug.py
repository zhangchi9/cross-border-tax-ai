import re
from pathlib import Path

# Read the markdown
content = Path("tax_team/knowledge_base/intake/questions.md").read_text(encoding='utf-8')

# Find gating questions section
gating_section = re.search(
    r'## Gating Questions\n(.*?)(?=\n## Module |$)',
    content,
    re.DOTALL
)

if gating_section:
    print("Gating section found!")
    print(f"Gating section length: {len(gating_section.group(1))}")

    # Test the question pattern
    question_pattern = r'### (.*?)\n- \*\*ID\*\*: `([^`]+)`\n- \*\*Action\*\*: (.*?)(?:\n- \*\*Quick Replies\*\*: (.*))?(?=\n\n|\n###|$)'

    matches = list(re.finditer(question_pattern, gating_section.group(1), re.DOTALL))
    print(f"\nFound {len(matches)} gating questions with current pattern")

    for i, match in enumerate(matches[:3]):
        print(f"\n--- Question {i+1} ---")
        print(f"Text: {match.group(1)[:50]}")
        print(f"ID: {match.group(2)}")
        print(f"Action: {match.group(3)[:50]}")

    # Show the section around the first question
    print("\n\n=== First 1000 chars of gating section ===")
    print(gating_section.group(1)[:1000])

    # Try a different pattern
    print("\n\n=== Testing alternative pattern ===")
    alt_pattern = r'### ([^\n]+)\n- \*\*ID\*\*: `([^`]+)`\n- \*\*Action\*\*: ([^\n]+)'
    alt_matches = list(re.finditer(alt_pattern, gating_section.group(1)))
    print(f"Found {len(alt_matches)} questions with alternative pattern")

    for i, match in enumerate(alt_matches[:5]):
        print(f"\n--- Question {i+1} ---")
        print(f"Text: {match.group(1)}")
        print(f"ID: {match.group(2)}")
        print(f"Action: {match.group(3)}")