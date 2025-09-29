"""
LLM-based Forms Analysis Agent
Analyzes tags to determine required tax forms and compliance obligations using LLM
"""
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import google.generativeai as genai
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_agent import TaxAgent
from app.config import settings


class LLMFormsAnalysisAgent(TaxAgent):
    """LLM-powered agent for analyzing tags and determining required forms"""

    def __init__(self):
        super().__init__("llm_forms_analysis_agent", "tags/definitions.json")
        self.model_provider = settings.AI_MODEL_PROVIDER

        # Initialize the appropriate AI client
        if self.model_provider == "openai":
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model_name = settings.OPENAI_MODEL
        elif self.model_provider == "gemini":
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self.model_name = settings.GEMINI_MODEL
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for forms analysis agent"""

        # Load tag definitions from knowledge base
        tag_definitions = self.knowledge_base.get("tag_definitions", {})

        tags_text = ""
        for tag_name, tag_info in tag_definitions.items():
            description = tag_info.get("description", "No description")
            forms = tag_info.get("forms", {})

            tags_text += f"\n**{tag_name}**: {description}\n"
            if forms:
                for jurisdiction, form_list in forms.items():
                    tags_text += f"  - {jurisdiction}: {', '.join(form_list)}\n"

        return f"""You are a specialized cross-border tax forms analysis agent. Your role is to analyze assigned tax tags and determine the required tax forms, compliance obligations, and provide comprehensive guidance.

KNOWLEDGE BASE - TAG DEFINITIONS AND FORMS:
{tags_text}

CORE RESPONSIBILITIES:
1. **Forms Analysis**: Analyze provided tags and determine all required tax forms across jurisdictions
2. **Compliance Assessment**: Evaluate complexity, deadlines, and compliance requirements
3. **Strategic Recommendations**: Provide actionable next steps and recommendations
4. **Risk Assessment**: Identify potential issues and areas requiring professional attention

ANALYSIS APPROACH:
- Map each provided tag to its corresponding forms using the knowledge base
- Consider jurisdictional requirements (US, Canadian, state/provincial)
- Assess form priorities based on deadlines and importance
- Identify interdependencies between different forms
- Evaluate overall complexity of the tax situation

FORM PRIORITY LEVELS:
- **High Priority**: Forms with immediate deadlines or severe penalties for non-compliance
- **Medium Priority**: Important forms with reasonable deadlines
- **Low Priority**: Informational or less time-sensitive forms

OUTPUT FORMAT:
Your response should be structured JSON with the following format:

```json
{
    "analysis_summary": "Brief overview of the analysis",
    "required_forms": [
        {
            "form": "Form Name",
            "jurisdiction": "US/Canada/State",
            "priority": "high/medium/low",
            "due_date": "YYYY-MM-DD or description",
            "description": "What this form is for"
        }
    ],
    "estimated_complexity": "high/medium/low",
    "priority_deadlines": [
        {
            "form": "Form Name",
            "jurisdiction": "US/Canada",
            "due_date": "YYYY-MM-DD or description"
        }
    ],
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ],
    "next_steps": [
        "Action item 1",
        "Action item 2"
    ],
    "compliance_checklist": [
        {
            "task": "Task description",
            "due_date": "YYYY-MM-DD or description",
            "status": "pending"
        }
    ]
}
```

ANALYSIS GUIDELINES:
- Be comprehensive but practical in form identification
- Consider current tax year (2024) deadlines where applicable
- Prioritize forms based on penalties and importance
- Provide actionable, specific recommendations
- Flag situations requiring professional tax help
- Consider treaty implications for cross-border situations

SAFETY AND ACCURACY:
- Only recommend forms that clearly map to the provided tags
- Be conservative with deadline estimates if uncertain
- Clearly indicate when professional consultation is recommended
- Focus on compliance and accuracy over speed
"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method for forms analysis"""
        handoff_data = input_data.get("handoff_data", {})
        case_summary = handoff_data.get("case_summary", "")
        tags = handoff_data.get("tags", [])
        client_profile = handoff_data.get("client_profile", {})

        self.logger.info(f"Analyzing tags: {tags}")

        if not tags:
            return {
                "analysis_summary": "No tags provided for analysis.",
                "required_forms": [],
                "estimated_complexity": "low",
                "recommendations": ["Please complete the intake process first."],
                "next_steps": ["Return to intake agent for information gathering."]
            }

        # Generate LLM analysis
        analysis_result = await self._generate_llm_analysis(tags, case_summary, client_profile)

        return analysis_result

    async def _generate_llm_analysis(self, tags: List[str], case_summary: str, client_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate forms analysis using LLM"""

        tags_text = ", ".join(tags)
        profile_text = json.dumps(client_profile, indent=2) if client_profile else "No additional profile information"

        prompt = f"""
ASSIGNED TAGS: {tags_text}

CASE SUMMARY: {case_summary}

CLIENT PROFILE:
{profile_text}

Please analyze these tags and provide a comprehensive forms analysis. Consider:

1. What tax forms are required based on these specific tags?
2. What are the priorities and deadlines for each form?
3. What is the overall complexity of this tax situation?
4. What are the most important next steps for the client?
5. What recommendations should be provided?

Use the knowledge base to map tags to forms accurately. Provide your analysis in the JSON format specified in the system prompt.
"""

        try:
            if self.model_provider == "openai":
                messages = [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]

                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.3,  # Lower temperature for more precise analysis
                    max_tokens=2000
                )

                response_text = response.choices[0].message.content

            elif self.model_provider == "gemini":
                full_prompt = f"{self._get_system_prompt()}\n\n{prompt}"
                response = self.model.generate_content(full_prompt)
                response_text = response.text

            # Parse JSON response
            analysis_result = self._parse_json_response(response_text)

            # Add metadata
            analysis_result["analyzed_tags"] = tags
            analysis_result["analysis_timestamp"] = datetime.now().isoformat()

            return analysis_result

        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return self._fallback_analysis(tags)

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, with fallback handling"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for JSON-like structure
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            parsed_result = json.loads(json_str)

            # Validate required fields
            required_fields = ["analysis_summary", "required_forms", "estimated_complexity"]
            for field in required_fields:
                if field not in parsed_result:
                    parsed_result[field] = self._get_default_value(field)

            return parsed_result

        except Exception as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            # Return structured fallback based on response text
            return self._extract_fallback_analysis(response_text)

    def _extract_fallback_analysis(self, response_text: str) -> Dict[str, Any]:
        """Extract analysis information from unstructured response"""
        # Basic fallback analysis
        return {
            "analysis_summary": "Analysis completed but response parsing encountered issues. Please review manually.",
            "required_forms": [],
            "estimated_complexity": "medium",
            "recommendations": [
                "Consult with a tax professional for detailed form requirements",
                "Review official tax authority guidelines"
            ],
            "next_steps": [
                "Gather required documentation",
                "Consider professional tax assistance"
            ],
            "priority_deadlines": [],
            "compliance_checklist": []
        }

    def _fallback_analysis(self, tags: List[str]) -> Dict[str, Any]:
        """Provide fallback analysis when LLM fails"""
        return {
            "analysis_summary": f"Basic analysis for tags: {', '.join(tags)}. LLM analysis unavailable.",
            "required_forms": [
                {
                    "form": "Consult Tax Professional",
                    "jurisdiction": "Both",
                    "priority": "high",
                    "due_date": "As soon as possible",
                    "description": "Professional consultation recommended due to analysis limitations"
                }
            ],
            "estimated_complexity": "high",
            "recommendations": [
                "Seek professional tax advice",
                "Review official tax forms and instructions"
            ],
            "next_steps": [
                "Contact a qualified tax professional",
                "Gather all relevant tax documents"
            ],
            "priority_deadlines": [],
            "compliance_checklist": [
                {
                    "task": "Schedule consultation with tax professional",
                    "due_date": "Within 1 week",
                    "status": "pending"
                }
            ],
            "analyzed_tags": tags,
            "analysis_timestamp": datetime.now().isoformat()
        }

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            "analysis_summary": "Analysis completed with available information.",
            "required_forms": [],
            "estimated_complexity": "medium",
            "recommendations": [],
            "next_steps": [],
            "priority_deadlines": [],
            "compliance_checklist": []
        }
        return defaults.get(field, "")

    def get_analysis_summary(self, tags: List[str]) -> Dict[str, Any]:
        """Get a quick summary of what this agent can analyze"""
        return {
            "agent_type": "llm_forms_analysis",
            "supported_tags": list(self.knowledge_base.get("tag_definitions", {}).keys()),
            "input_tags": tags,
            "analysis_capabilities": [
                "Form identification and mapping",
                "Compliance deadlines assessment",
                "Complexity evaluation",
                "Strategic recommendations",
                "Next steps planning"
            ]
        }