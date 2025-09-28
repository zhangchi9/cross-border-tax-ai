"""
Knowledge Base module for tax consultant AI agent.
Provides access to structured tax data and scenarios.
"""

import csv
import os
from typing import List, Dict, Optional
from pathlib import Path


class KnowledgeBase:
    """Access to tax scenarios and reference data."""

    def __init__(self):
        # Use absolute path from app directory
        self.data_dir = Path("/app/data/knowledge_base")
        self.scenarios_file = self.data_dir / "scenarios" / "US-Canada_Cross-Border_Tax_Scenarios_With_Strategies.csv"

    def load_scenarios(self) -> List[Dict[str, str]]:
        """Load all tax scenarios from CSV."""
        scenarios = []

        if not self.scenarios_file.exists():
            return scenarios

        try:
            with open(self.scenarios_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scenarios.append(dict(row))
        except Exception as e:
            print(f"Error loading scenarios: {e}")

        return scenarios

    def search_scenarios_by_category(self, category: str) -> List[Dict[str, str]]:
        """Search scenarios by category."""
        scenarios = self.load_scenarios()
        return [s for s in scenarios if category.lower() in s.get('Category', '').lower()]

    def search_scenarios_by_keyword(self, keyword: str) -> List[Dict[str, str]]:
        """Search scenarios by keyword in scenario description."""
        scenarios = self.load_scenarios()
        keyword_lower = keyword.lower()

        matching_scenarios = []
        for scenario in scenarios:
            # Search in multiple fields
            searchable_text = " ".join([
                scenario.get('Scenario', ''),
                scenario.get("Tom's Situation", ''),
                scenario.get('Best Strategy', ''),
                scenario.get('Category', '')
            ]).lower()

            if keyword_lower in searchable_text:
                matching_scenarios.append(scenario)

        return matching_scenarios

    def get_scenario_by_id(self, scenario_id: str) -> Optional[Dict[str, str]]:
        """Get a specific scenario by ID."""
        scenarios = self.load_scenarios()
        for scenario in scenarios:
            if scenario.get('ID') == str(scenario_id):
                return scenario
        return None

    def get_forms_for_scenario(self, scenario_id: str) -> List[str]:
        """Extract forms mentioned in a scenario."""
        scenario = self.get_scenario_by_id(scenario_id)
        if not scenario:
            return []

        forms_text = scenario.get('Key Forms/Elections', '')
        # Simple parsing - could be enhanced
        forms = [f.strip() for f in forms_text.split(';') if f.strip()]
        return forms

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        scenarios = self.load_scenarios()
        categories = set()
        for scenario in scenarios:
            category = scenario.get('Category', '').strip()
            if category:
                categories.add(category)
        return sorted(list(categories))


# Create a global instance for easy access
knowledge_base = KnowledgeBase()