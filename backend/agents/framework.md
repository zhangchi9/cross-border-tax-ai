# Cross-Border Tax Agentic Framework

## Overview
A two-agent system for cross-border tax consultation and form analysis, leveraging the knowledge base for intelligent tax guidance.

## Agent Architecture

### Agent 1: Intake Agent
**Purpose**: Interactive client consultation to gather tax situation details and assign relevant tags

**Capabilities**:
- Conversational intake process using natural language
- Dynamic question selection based on client responses
- Smart question skipping when information is irrelevant
- Tag assignment based on client situation
- Case summary generation

**Knowledge Sources**:
- `intake/questions.json` - Question templates and routing logic
- Gating questions for module determination
- Module-specific questions for detailed analysis

**Input**: Client responses (text/conversational)
**Output**:
```json
{
  "case_summary": "Detailed summary of client's tax situation",
  "tags": ["tag1", "tag2", "tag3"],
  "client_profile": {
    "us_person": true,
    "canadian_resident": false,
    "primary_concerns": ["employment", "real_estate"]
  },
  "conversation_context": "Key details from conversation"
}
```

### Agent 2: Forms Analysis Agent
**Purpose**: Analyze assigned tags to determine required tax forms and compliance obligations

**Capabilities**:
- Tag-to-forms mapping analysis
- Jurisdiction-specific form requirements
- Form prioritization and dependencies
- Compliance timeline generation
- Form-specific guidance provision

**Knowledge Sources**:
- `tags/definitions.json` - Tag definitions and form mappings
- Forms database with requirements and instructions

**Input**: Tags and case summary from Agent 1
**Output**:
```json
{
  "required_forms": [
    {
      "form": "Form 1040",
      "jurisdiction": "US",
      "priority": "high",
      "due_date": "April 15",
      "reason": "U.S. person worldwide filing requirement"
    }
  ],
  "compliance_checklist": [...],
  "estimated_complexity": "medium",
  "recommendations": [...]
}
```

## Agent Communication Protocol

### 1. Session Initialization
```json
{
  "session_id": "uuid",
  "timestamp": "2024-01-01T00:00:00Z",
  "client_id": "optional"
}
```

### 2. Agent 1 → Agent 2 Handoff
```json
{
  "session_id": "uuid",
  "agent_1_output": {
    "case_summary": "...",
    "tags": [...],
    "client_profile": {...},
    "confidence_score": 0.85
  }
}
```

### 3. Agent 2 Response
```json
{
  "session_id": "uuid",
  "agent_2_output": {
    "required_forms": [...],
    "compliance_checklist": [...],
    "recommendations": [...]
  }
}
```

## Implementation Strategy

### Phase 1: Agent 1 (Intake Agent)
1. **Question Selection Engine**
   - Parse gating questions to determine relevant modules
   - Implement intelligent question skipping logic
   - Create context-aware follow-up questions

2. **Conversation Management**
   - Natural language processing for client responses
   - Context preservation across conversation turns
   - Tag assignment based on responses

3. **Case Summary Generation**
   - Extract key facts from conversation
   - Generate structured summary
   - Assign confidence scores to tags

### Phase 2: Agent 2 (Forms Analysis Agent)
1. **Tag Analysis Engine**
   - Map tags to form requirements using definitions.json
   - Handle tag combinations and conflicts
   - Determine jurisdiction-specific requirements

2. **Form Prioritization**
   - Rank forms by importance and deadlines
   - Identify dependencies between forms
   - Generate compliance timeline

3. **Guidance Generation**
   - Provide form-specific instructions
   - Highlight critical deadlines
   - Suggest optimization strategies

## Technical Architecture

### Agent Base Class
```python
class TaxAgent:
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base = self.load_knowledge_base(knowledge_base_path)

    def process(self, input_data: dict) -> dict:
        raise NotImplementedError

    def load_knowledge_base(self, path: str) -> dict:
        # Load and parse JSON knowledge base
        pass
```

### Agent 1: IntakeAgent
```python
class IntakeAgent(TaxAgent):
    def __init__(self):
        super().__init__("intake/questions.json")
        self.conversation_context = {}
        self.assigned_tags = []

    def process_client_response(self, response: str) -> dict:
        # Analyze response and determine next question
        # Assign tags based on responses
        # Generate follow-up questions
        pass

    def generate_case_summary(self) -> dict:
        # Create structured summary of client situation
        pass
```

### Agent 2: FormsAnalysisAgent
```python
class FormsAnalysisAgent(TaxAgent):
    def __init__(self):
        super().__init__("tags/definitions.json")

    def analyze_tags(self, tags: list, case_summary: str) -> dict:
        # Map tags to required forms
        # Determine compliance requirements
        # Generate recommendations
        pass

    def prioritize_forms(self, forms: list) -> list:
        # Sort by priority and deadlines
        pass
```

## Workflow Example

1. **Client Interaction Starts**
   ```
   Client: "I'm a U.S. citizen living in Canada with rental property in both countries"
   ```

2. **Agent 1 Processing**
   - Identifies: US person ✓, Canadian resident ✓, Real estate ✓
   - Asks targeted follow-up questions about rental income, residency status, etc.
   - Assigns tags: ["us_person_worldwide_filing", "canadian_us_rental", "us_person_canadian_rental"]

3. **Agent 1 → Agent 2 Handoff**
   ```json
   {
     "case_summary": "U.S. citizen residing in Canada with rental properties in both countries...",
     "tags": ["us_person_worldwide_filing", "canadian_us_rental", "us_person_canadian_rental"],
     "client_profile": {"us_person": true, "canadian_resident": true}
   }
   ```

4. **Agent 2 Analysis**
   - Maps tags to forms: Form 1040, Form 1116, Schedule E, T1, Section 216 return
   - Prioritizes by deadlines and importance
   - Generates compliance checklist

5. **Final Output**
   ```json
   {
     "required_forms": [
       {"form": "Form 1040", "priority": "high", "due_date": "April 15"},
       {"form": "T1 General", "priority": "high", "due_date": "April 30"}
     ],
     "recommendations": ["Consider Section 871(d) election for U.S. rental", "File NR6 for Canadian rental"]
   }
   ```

## Benefits

1. **Intelligent Questioning**: Agent 1 only asks relevant questions, improving user experience
2. **Accurate Analysis**: Agent 2 provides comprehensive form requirements based on exact client situation
3. **Scalable Knowledge**: Easy to update knowledge base without changing agent logic
4. **Modular Design**: Each agent can be improved independently
5. **Audit Trail**: Complete record of reasoning and tag assignments