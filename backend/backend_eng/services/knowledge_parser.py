"""
Knowledge Base Parser

Parses markdown files from tax_team/ into JSON format for science team consumption.

Owner: Backend Engineering Team
"""
import re
import json
from pathlib import Path
from typing import Dict, Any, List


class KnowledgeBaseParser:
    """Parser for tax team markdown files"""

    def __init__(self, tax_team_dir: Path = None, cache_dir: Path = None):
        """
        Initialize parser

        Args:
            tax_team_dir: Path to tax_team/knowledge_base directory
            cache_dir: Path to cache directory for parsed JSON
        """
        if tax_team_dir is None:
            tax_team_dir = Path(__file__).parent.parent.parent / "tax_team" / "knowledge_base"
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "knowledge_cache"

        self.tax_team_dir = Path(tax_team_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def parse_all(self) -> Dict[str, Any]:
        """
        Parse all markdown files and return complete knowledge base

        Returns:
            Complete knowledge base dictionary
        """
        knowledge_base = {
            "intake": self.parse_intake_questions(),
            "tags": self.parse_tag_definitions()
        }

        # Write to cache
        self._write_cache(knowledge_base)

        return knowledge_base

    def parse_intake_questions(self) -> Dict[str, Any]:
        """
        Parse intake/questions.md into JSON format

        Returns:
            Dictionary with gating_questions and modules
        """
        questions_file = self.tax_team_dir / "intake" / "questions.md"

        if not questions_file.exists():
            return {"gating_questions": {"questions": []}, "modules": {}}

        content = questions_file.read_text(encoding='utf-8')

        # Parse gating questions
        gating_questions = self._parse_gating_questions(content)

        # Parse module questions
        modules = self._parse_modules(content)

        return {
            "gating_questions": {
                "title": "Gating questions",
                "description": "Initial screening questions to determine which modules apply",
                "questions": gating_questions
            },
            "modules": modules
        }

    def _parse_gating_questions(self, content: str) -> List[Dict[str, Any]]:
        """Parse gating questions section"""
        questions = []

        # Find gating questions section
        gating_section = re.search(
            r'## Gating Questions\n(.*?)(?=\n## Module |$)',
            content,
            re.DOTALL
        )

        if not gating_section:
            return questions

        # Parse each question
        question_pattern = r'### (.*?)\n- \*\*ID\*\*: `([^`]+)`\n- \*\*Action\*\*: (.*?)(?:\n- \*\*Quick Replies\*\*: (.*))?(?=\n\n|\n###|$)'

        for match in re.finditer(question_pattern, gating_section.group(1), re.DOTALL):
            question_text = match.group(1).strip()
            question_id = match.group(2).strip()
            action = match.group(3).strip()
            quick_replies = match.group(4)

            questions.append({
                "id": question_id,
                "question": question_text,
                "action": action
            })

        return questions

    def _parse_modules(self, content: str) -> Dict[str, Any]:
        """Parse module sections"""
        modules = {}

        # Find all module sections
        module_pattern = r'## Module ([A-Z]) — (.*?)\n(.*?)(?=\n## Module |---\n\n## Notes|$)'

        for match in re.finditer(module_pattern, content, re.DOTALL):
            module_letter = match.group(1)
            module_title = match.group(2).strip()
            module_content = match.group(3)

            # Create module ID
            module_id = self._module_title_to_id(module_title)

            # Parse questions in this module
            questions = self._parse_module_questions(module_content)

            modules[module_id] = {
                "id": f"module_{module_letter.lower()}",
                "title": f"Module {module_letter} — {module_title}",
                "questions": questions
            }

        return modules

    def _parse_module_questions(self, module_content: str) -> List[Dict[str, Any]]:
        """Parse questions within a module"""
        questions = []

        # Pattern for module questions (similar to gating questions)
        question_pattern = r'###+ (.*?)\n(?:- \*\*ID\*\*: `([^`]+)`\n)?- \*\*Action\*\*: (.*?)(?:\n- \*\*Quick Replies\*\*: (.*))?(?=\n\n|\n###|$)'

        for match in re.finditer(question_pattern, module_content, re.DOTALL):
            question_text = match.group(1).strip()
            question_id = match.group(2).strip() if match.group(2) else ""
            action = match.group(3).strip()
            quick_replies = match.group(4)

            if question_id:  # Only include if has ID
                questions.append({
                    "id": question_id,
                    "question": question_text,
                    "action": action
                })

        return questions

    def parse_tag_definitions(self) -> Dict[str, Any]:
        """
        Parse tags/definitions.md into JSON format

        Returns:
            Dictionary with tag definitions
        """
        tags_file = self.tax_team_dir / "tags" / "definitions.md"

        if not tags_file.exists():
            return {"tag_definitions": {}}

        content = tags_file.read_text(encoding='utf-8')

        tag_definitions = {}

        # Parse each tag
        tag_pattern = r'### ([a-z_]+)\n\n\*\*Name\*\*: (.*?)\n\n\*\*Description\*\*: (.*?)\n\n\*\*Forms:\*\*(.*?)\*\*Why\*\*: (.*?)(?=\n\n---|###|$)'

        for match in re.finditer(tag_pattern, content, re.DOTALL):
            tag_id = match.group(1).strip()
            name = match.group(2).strip()
            description = match.group(3).strip()
            forms_section = match.group(4).strip()
            why = match.group(5).strip()

            # Parse forms by jurisdiction
            forms = self._parse_forms_section(forms_section)

            tag_definitions[tag_id] = {
                "id": tag_id,
                "name": name,
                "description": description,
                "forms": forms,
                "why": why
            }

        return {"tag_definitions": tag_definitions}

    def _parse_forms_section(self, forms_section: str) -> Dict[str, List[Any]]:
        """Parse forms section by jurisdiction"""
        forms_by_jurisdiction = {}

        # Parse by jurisdiction (### United States, ### Canada, etc.)
        jurisdiction_pattern = r'### (.*?)\n(.*?)(?=\n###|$)'

        for match in re.finditer(jurisdiction_pattern, forms_section, re.DOTALL):
            jurisdiction = match.group(1).strip()
            forms_text = match.group(2).strip()

            # Parse individual forms
            form_pattern = r'- \*\*(.*?)\*\*: (.*?)(?=\n-|\n###|$)'
            forms_list = []

            for form_match in re.finditer(form_pattern, forms_text, re.DOTALL):
                form_name = form_match.group(1).strip()
                form_note = form_match.group(2).strip()

                forms_list.append({
                    "form": form_name,
                    "note": form_note
                })

            # Normalize jurisdiction key
            jurisdiction_key = jurisdiction.lower().replace(" ", "_")
            if "united states" in jurisdiction.lower():
                jurisdiction_key = "us"
            elif "canada" in jurisdiction.lower():
                jurisdiction_key = "ca"

            forms_by_jurisdiction[jurisdiction_key] = forms_list

        return forms_by_jurisdiction

    def _module_title_to_id(self, title: str) -> str:
        """Convert module title to ID"""
        # Simple mapping for common modules
        mapping = {
            "Residency & Elections": "residency_elections",
            "Employment & U.S. States": "employment_states",
            "Business & Entities": "business_entities",
            "Real Estate": "real_estate",
            "Investments & Financial Assets": "investments_financial",
            "Pensions, Savings & Social Benefits": "pensions_savings",
            "Equity Compensation": "equity_compensation",
            "Estates, Gifts & Trusts": "estates_gifts_trusts",
            "Reporting & Cleanup": "reporting_cleanup"
        }
        return mapping.get(title, title.lower().replace(" ", "_").replace("&", "and"))

    def _write_cache(self, knowledge_base: Dict[str, Any]) -> None:
        """Write parsed knowledge base to cache"""
        # Write intake questions
        intake_cache = self.cache_dir / "intake"
        intake_cache.mkdir(parents=True, exist_ok=True)
        with open(intake_cache / "questions.json", 'w', encoding='utf-8') as f:
            json.dump(knowledge_base["intake"], f, indent=2)

        # Write tag definitions
        tags_cache = self.cache_dir / "tags"
        tags_cache.mkdir(parents=True, exist_ok=True)
        with open(tags_cache / "definitions.json", 'w', encoding='utf-8') as f:
            json.dump(knowledge_base["tags"], f, indent=2)

    def watch_and_regenerate(self):
        """
        Watch for changes in tax_team directory and regenerate cache

        TODO: Implement file watching using watchdog library
        """
        # This would use the watchdog library to watch for file changes
        # and automatically regenerate the JSON cache
        pass


# Convenience function
def parse_knowledge_base() -> Dict[str, Any]:
    """
    Parse knowledge base and return JSON

    Returns:
        Complete knowledge base dictionary
    """
    parser = KnowledgeBaseParser()
    return parser.parse_all()


if __name__ == "__main__":
    # Test the parser
    parser = KnowledgeBaseParser()
    kb = parser.parse_all()
    print("Knowledge base parsed successfully!")
    print(f"Gating questions: {len(kb['intake']['gating_questions']['questions'])}")
    print(f"Modules: {len(kb['intake']['modules'])}")
    print(f"Tags: {len(kb['tags']['tag_definitions'])}")