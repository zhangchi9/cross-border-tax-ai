"""
Validation script for knowledge base consistency

This script validates that questions.md and definitions.md are consistent:
- All tag references have definitions
- All question IDs are unique
- All module references are valid
- Action formats are correct
- No critical issues

Exit codes:
0 - All validations passed
1 - Critical errors found
2 - Warnings only

Usage:
    python validate_knowledge_base.py
    python validate_knowledge_base.py --strict  # Treat warnings as errors
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_error(self, message: str):
        self.errors.append(f"[ERROR] {message}")

    def add_warning(self, message: str):
        self.warnings.append(f"[WARNING] {message}")

    def add_info(self, message: str):
        self.info.append(f"[INFO] {message}")

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def print_report(self):
        print("=" * 80)
        print("KNOWLEDGE BASE VALIDATION REPORT")
        print("=" * 80)

        if self.info:
            print("\n[INFORMATION]")
            for msg in self.info:
                print(f"  {msg}")

        if self.warnings:
            print(f"\n[WARNINGS] ({len(self.warnings)} found)")
            for msg in self.warnings:
                print(f"  {msg}")

        if self.errors:
            print(f"\n[ERRORS] ({len(self.errors)} found)")
            for msg in self.errors:
                print(f"  {msg}")

        print("\n" + "=" * 80)
        if self.has_errors():
            print("VALIDATION FAILED - Please fix errors above")
            print("=" * 80)
            return False
        elif self.has_warnings():
            print("VALIDATION PASSED WITH WARNINGS")
            print("=" * 80)
            return True
        else:
            print("VALIDATION PASSED - All checks successful")
            print("=" * 80)
            return True


def extract_tags_from_questions(content: str) -> Set[str]:
    """Extract all tag references from questions.md"""
    tags = set()

    # Pattern: Add tag `tag_name`
    pattern = r'Add tag `([^`]+)`'
    tags.update(re.findall(pattern, content))

    return tags


def extract_defined_tags(content: str) -> Set[str]:
    """Extract all defined tags from definitions.md"""
    tags = set()

    # Tags are defined as ### tag_name
    lines = content.split('\n')
    for line in lines:
        if line.startswith('### ') and not line.startswith('#### '):
            tag = line[4:].strip()
            # Skip jurisdiction headers
            if tag and tag not in ['United States', 'Canada', 'United States (State)']:
                tags.add(tag)

    return tags


def extract_all_questions(content: str) -> List[Dict]:
    """Extract all questions with their metadata"""
    questions = []
    lines = content.split('\n')
    current_question = {}
    current_section = None

    for i, line in enumerate(lines):
        # Track sections
        if line.startswith('## '):
            current_section = line[3:].strip()
            continue

        # New question
        if line.startswith('### ') or line.startswith('#### '):
            if current_question and 'id' in current_question:
                current_question['section'] = current_section
                questions.append(current_question)

            current_question = {
                'question': line.strip('# ').strip(),
                'line': i + 1
            }

        # Extract ID
        elif line.startswith('- **ID**:'):
            id_match = re.search(r'`([^`]+)`', line)
            if id_match:
                current_question['id'] = id_match.group(1)
            else:
                current_question['id'] = line.split(':', 1)[1].strip()

        # Extract Action
        elif line.startswith('- **Action**:'):
            current_question['action'] = line.split(':', 1)[1].strip()

    # Don't forget the last question
    if current_question and 'id' in current_question:
        current_question['section'] = current_section
        questions.append(current_question)

    return questions


def validate_unique_ids(questions: List[Dict], result: ValidationResult):
    """Validate that all question IDs are unique"""
    id_counts = defaultdict(list)

    for q in questions:
        if 'id' in q:
            id_counts[q['id']].append(q)

    duplicates = {qid: qs for qid, qs in id_counts.items() if len(qs) > 1}

    if duplicates:
        for qid, qs in duplicates.items():
            sections = [q.get('section', 'Unknown') for q in qs]
            result.add_error(f"Duplicate question ID '{qid}' found in sections: {', '.join(sections)}")
    else:
        result.add_info(f"All {len(questions)} question IDs are unique")


def validate_tag_references(questions: List[Dict], defined_tags: Set[str], result: ValidationResult):
    """Validate that all tag references exist in definitions"""
    referenced_tags = set()
    missing_tags = []

    for q in questions:
        action = q.get('action', '')
        if 'Add tag' in action:
            # Extract tags from action
            tag_matches = re.findall(r'`([^`]+)`', action)
            for tag in tag_matches:
                referenced_tags.add(tag)
                if tag not in defined_tags and tag != 'tag_name':  # Ignore template placeholder
                    missing_tags.append({
                        'tag': tag,
                        'question_id': q.get('id', 'unknown'),
                        'section': q.get('section', 'unknown')
                    })

    if missing_tags:
        for item in missing_tags:
            result.add_error(
                f"Tag '{item['tag']}' referenced in question '{item['question_id']}' "
                f"(section: {item['section']}) but not defined in definitions.md"
            )
    else:
        result.add_info(f"All {len(referenced_tags)} referenced tags have definitions")


def validate_action_format(questions: List[Dict], result: ValidationResult):
    """Validate that action fields are properly formatted"""
    issues = []

    for q in questions:
        action = q.get('action', '')
        qid = q.get('id', 'unknown')

        if not action:
            issues.append(f"Question '{qid}' has no action specified")
            continue

        # Check for valid action patterns
        valid_patterns = [
            r'Add tag `[^`]+`',  # Add tag `tag_name`
            r'Go to Module',      # Go to Module X
        ]

        has_valid_pattern = any(re.search(pattern, action) for pattern in valid_patterns)

        if not has_valid_pattern:
            result.add_warning(f"Question '{qid}' has unclear action format: {action[:50]}...")

    if issues:
        for issue in issues:
            result.add_error(issue)
    else:
        result.add_info(f"All {len(questions)} questions have action fields")


def validate_module_references(questions: List[Dict], result: ValidationResult):
    """Validate that module references are consistent"""
    valid_modules = [
        'Module A',
        'Module B',
        'Module C',
        'Module D',
        'Module E',
        'Module F',
        'Module G',
        'Module H',
        'Module I',
    ]

    module_refs = []

    for q in questions:
        action = q.get('action', '')
        if 'Go to Module' in action:
            # Extract module reference
            module_match = re.search(r'Module ([A-I])', action)
            if module_match:
                module_refs.append(module_match.group(0))
            else:
                result.add_warning(f"Question '{q.get('id', 'unknown')}' has unclear module reference")

    result.add_info(f"Found {len(module_refs)} module references")


def validate_tag_definitions(content: str, result: ValidationResult):
    """Validate that tag definitions are properly formatted"""
    tags = extract_defined_tags(content)

    for tag in tags:
        # Find the tag definition
        pattern = f"### {re.escape(tag)}\n\n\\*\\*Name\\*\\*:"
        if not re.search(pattern, content):
            result.add_warning(f"Tag '{tag}' definition missing '**Name**:' field")

        pattern = f"### {re.escape(tag)}.*?\\*\\*Description\\*\\*:"
        if not re.search(pattern, content, re.DOTALL):
            result.add_warning(f"Tag '{tag}' definition missing '**Description**:' field")

        pattern = f"### {re.escape(tag)}.*?\\*\\*Forms:\\*\\*"
        if not re.search(pattern, content, re.DOTALL):
            result.add_warning(f"Tag '{tag}' definition missing '**Forms:**' field")

        pattern = f"### {re.escape(tag)}.*?\\*\\*Why\\*\\*:"
        if not re.search(pattern, content, re.DOTALL):
            result.add_warning(f"Tag '{tag}' definition missing '**Why**:' field")

    result.add_info(f"Validated structure of {len(tags)} tag definitions")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Validate knowledge base consistency')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    args = parser.parse_args()

    result = ValidationResult()

    # Read files
    base_path = Path(__file__).parent / "tax_team" / "knowledge_base"
    questions_path = base_path / "intake" / "questions.md"
    definitions_path = base_path / "tags" / "definitions.md"

    try:
        with open(questions_path, 'r', encoding='utf-8') as f:
            questions_content = f.read()
    except FileNotFoundError:
        result.add_error(f"questions.md not found at {questions_path}")
        result.print_report()
        return 1

    try:
        with open(definitions_path, 'r', encoding='utf-8') as f:
            definitions_content = f.read()
    except FileNotFoundError:
        result.add_error(f"definitions.md not found at {definitions_path}")
        result.print_report()
        return 1

    # Extract data
    questions = extract_all_questions(questions_content)
    defined_tags = extract_defined_tags(definitions_content)

    result.add_info(f"Loaded {len(questions)} questions")
    result.add_info(f"Loaded {len(defined_tags)} tag definitions")

    # Run validations
    validate_unique_ids(questions, result)
    validate_tag_references(questions, defined_tags, result)
    validate_action_format(questions, result)
    validate_module_references(questions, result)
    validate_tag_definitions(definitions_content, result)

    # Print report
    success = result.print_report()

    # Determine exit code
    if result.has_errors():
        return 1
    elif args.strict and result.has_warnings():
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
