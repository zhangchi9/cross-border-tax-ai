"""
Audit knowledge base files to identify missing tags and inconsistencies

This script analyzes questions.md and definitions.md to find:
- Tags referenced in questions but not defined
- Inconsistencies in formatting
- Missing mappings
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_tags_from_questions(questions_content):
    """Extract all tag references from questions.md"""
    tags_referenced = set()

    # Pattern 1: "Add tag `tag_name`"
    pattern1 = r'Add tag `([^`]+)`'
    tags_referenced.update(re.findall(pattern1, questions_content))

    # Pattern 2: Look for tags in action field
    # Split by questions and parse each
    lines = questions_content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('- **Action**:'):
            # Extract tag if mentioned
            matches = re.findall(r'`([a-z_]+)`', line)
            tags_referenced.update(matches)

    return tags_referenced

def extract_defined_tags(definitions_content):
    """Extract all defined tags from definitions.md"""
    defined_tags = set()

    # Tags are defined as ### tag_name (three hashes)
    # Section headers use ## (two hashes)
    skip_headers = ['Notes for Tax Team', 'Format Guide', 'Adding New Tags']

    lines = definitions_content.split('\n')
    for line in lines:
        if line.startswith('### '):
            tag = line[4:].strip()
            # Skip non-tag headers
            if tag not in skip_headers and not tag.endswith('Tags') and tag != '':
                defined_tags.add(tag)

    return defined_tags

def extract_gating_questions(questions_content):
    """Extract gating questions and their actions"""
    gating_questions = []

    lines = questions_content.split('\n')
    current_question = {}
    in_gating_section = False

    for i, line in enumerate(lines):
        if '## Gating Questions' in line:
            in_gating_section = True
            continue

        if in_gating_section and line.startswith('## Module'):
            break

        if in_gating_section and line.startswith('### '):
            # New question
            if current_question:
                gating_questions.append(current_question)
            current_question = {'question': line[4:].strip()}

        elif in_gating_section and line.startswith('- **ID**:'):
            current_question['id'] = line.split('`')[1] if '`' in line else line.split(':')[1].strip()

        elif in_gating_section and line.startswith('- **Action**:'):
            current_question['action'] = line.split(':', 1)[1].strip()

    if current_question:
        gating_questions.append(current_question)

    return gating_questions

def extract_module_questions(questions_content):
    """Extract module questions and their tag actions"""
    module_questions = []

    lines = questions_content.split('\n')
    current_question = {}
    current_module = None

    for i, line in enumerate(lines):
        if line.startswith('## Module '):
            current_module = line.strip()
            continue

        if line == '---' and current_module:
            current_module = None
            continue

        if current_module and line.startswith('### ') or (current_module and line.startswith('#### ')):
            # New question
            if current_question and 'id' in current_question:
                module_questions.append(current_question)
            current_question = {'question': line.strip('# ').strip(), 'module': current_module}

        elif current_module and line.startswith('- **ID**:'):
            current_question['id'] = line.split('`')[1] if '`' in line else line.split(':')[1].strip()

        elif current_module and line.startswith('- **Action**:'):
            current_question['action'] = line.split(':', 1)[1].strip()

    if current_question and 'id' in current_question:
        module_questions.append(current_question)

    return module_questions

def main():
    # Read files
    base_path = Path(__file__).parent / "tax_team" / "knowledge_base"

    questions_path = base_path / "intake" / "questions.md"
    definitions_path = base_path / "tags" / "definitions.md"

    with open(questions_path, 'r', encoding='utf-8') as f:
        questions_content = f.read()

    with open(definitions_path, 'r', encoding='utf-8') as f:
        definitions_content = f.read()

    # Extract information
    tags_referenced = extract_tags_from_questions(questions_content)
    defined_tags = extract_defined_tags(definitions_content)
    gating_questions = extract_gating_questions(questions_content)
    module_questions = extract_module_questions(questions_content)

    # Analysis
    missing_tags = tags_referenced - defined_tags
    unused_tags = defined_tags - tags_referenced

    print("=" * 80)
    print("KNOWLEDGE BASE AUDIT REPORT")
    print("=" * 80)

    print(f"\n[STATISTICS]")
    print(f"   - Tags referenced in questions: {len(tags_referenced)}")
    print(f"   - Tags defined in definitions.md: {len(defined_tags)}")
    print(f"   - Gating questions: {len(gating_questions)}")
    print(f"   - Module questions: {len(module_questions)}")

    if missing_tags:
        print(f"\n[ERROR] MISSING TAG DEFINITIONS ({len(missing_tags)}):")
        print("   These tags are referenced in questions.md but not defined in definitions.md:")
        for tag in sorted(missing_tags):
            print(f"   - {tag}")
    else:
        print(f"\n[OK] No missing tag definitions")

    if unused_tags:
        print(f"\n[WARNING] UNUSED TAG DEFINITIONS ({len(unused_tags)}):")
        print("   These tags are defined but never referenced in questions:")
        for tag in sorted(unused_tags):
            print(f"   - {tag}")

    # Check gating questions for tag assignments
    print(f"\n[GATING QUESTIONS ANALYSIS]")
    gating_without_tags = []
    gating_with_tags = []

    for q in gating_questions:
        action = q.get('action', '')
        has_tag = 'tag' in action.lower() or any(tag in action for tag in defined_tags)

        if has_tag:
            gating_with_tags.append(q)
        else:
            gating_without_tags.append(q)

    print(f"\n   [OK] Gating questions WITH tag assignment: {len(gating_with_tags)}")
    for q in gating_with_tags:
        print(f"      - {q['id']}: {q.get('action', 'No action')}")

    print(f"\n   [ERROR] Gating questions WITHOUT tag assignment: {len(gating_without_tags)}")
    print("      These should probably assign foundational tags:")
    for q in gating_without_tags:
        print(f"      - {q['id']}: {q.get('action', 'No action')}")

    # Check module questions
    print(f"\n[MODULE QUESTIONS ANALYSIS]")
    module_without_tags = []

    for q in module_questions:
        action = q.get('action', '')
        has_tag = 'Add tag' in action

        if not has_tag and action:
            module_without_tags.append(q)

    if module_without_tags:
        print(f"   [WARNING] Module questions without tag actions: {len(module_without_tags)}")
        for q in module_without_tags[:10]:  # Show first 10
            print(f"      - {q['id']}: {q.get('action', 'No action')}")
    else:
        print(f"   [OK] All module questions have tag actions")

    print("\n" + "=" * 80)
    print("END OF AUDIT")
    print("=" * 80)

if __name__ == "__main__":
    main()
