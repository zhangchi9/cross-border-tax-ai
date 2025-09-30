# Science Module

## Owner
**Science/ML Team**

## Purpose
This module contains all AI/ML functionality for the cross-border tax consultation application. It provides the core conversational AI workflow using LangGraph.

## Architecture

```
science/
├── agents/                 # LangGraph workflow components
│   ├── workflow.py         # Main workflow orchestration
│   ├── state.py            # State management
│   ├── nodes.py            # AI nodes (Intake, FormsAnalysis, Completion)
│   └── prompts.py          # LLM prompt templates
├── services/
│   └── llm_service.py      # LLM initialization
├── config.py               # AI model configuration
└── requirements.txt        # Science-specific dependencies
```

## Key Components

### 1. Workflow (`agents/workflow.py`)
- LangGraph-based state machine
- Manages conversation flow through intake → forms analysis → completion
- Handles session persistence via MemorySaver

### 2. Nodes (`agents/nodes.py`)
- **IntakeNode**: Asks questions, assigns tags based on responses
- **FormsAnalysisNode**: Generates form requirements based on tags
- **CompletionNode**: Handles follow-up questions after analysis

### 3. Prompts (`agents/prompts.py`)
- Centralized LLM prompt templates
- Separated for easier experimentation and A/B testing

## Configuration

Edit `config.py` to change AI models:

```python
AI_MODEL_PROVIDER = "openai"  # or "gemini"
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "models/gemini-1.5-flash-latest"
LLM_TEMPERATURE = 0.1
```

## Running Independently

The science module can be run independently for testing:

```python
import asyncio
from science.agents import TaxConsultationWorkflow

async def test():
    workflow = TaxConsultationWorkflow()
    result = await workflow.start_consultation("I need help with US-Canada taxes")
    print(result)

asyncio.run(test())
```

## Development

### Install dependencies
```bash
pip install -r requirements.txt
```

### Test workflow
```bash
python -c "from science.agents import TaxConsultationWorkflow; print('Import successful')"
```

## Integration

Backend engineering team integrates this module via:

```python
from science.agents import TaxConsultationWorkflow

workflow = TaxConsultationWorkflow()
result = await workflow.continue_consultation(session_id, message)
```

## Knowledge Base

This module reads knowledge base from:
- **Current**: `backend/data/knowledge_base/*.json`
- **Future**: Parsed JSON from `backend_eng/knowledge_cache/` (generated from tax team's markdown)

## Responsibilities

✅ **Science Team Owns:**
- LangGraph workflow logic
- LLM prompt engineering
- Model selection and configuration
- AI node behavior
- Conversation flow routing

❌ **Science Team Does NOT Own:**
- API endpoints (backend_eng responsibility)
- Frontend integration (backend_eng responsibility)
- Knowledge base content (tax team responsibility)
- Session management persistence (backend_eng responsibility)

## Key Metrics

Monitor these for model performance:
- Average tags assigned per conversation
- Transition timing (intake → forms analysis)
- Forms analysis accuracy
- Conversation length before completion

## Deployment

Can be deployed independently as a service:

```bash
# Future: Science team API service
uvicorn science.api:app --port 8001
```

Currently integrated into backend_eng deployment.