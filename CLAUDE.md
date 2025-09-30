# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A cross-border tax consultation web application using conversational AI. The backend has been restructured into **three independent modules** with clear team ownership:

- **science/** - AI/ML team owns LangGraph workflow and AI logic
- **backend_eng/** - Backend engineering team owns API orchestration and integration
- **tax_team/** - Tax experts own knowledge content in human-readable markdown

**Core Architecture:** Tax team markdown → Backend eng parser → Science AI workflow → API → Frontend

## Development Commands

### Backend - Three Module Structure

The backend is now split into three modules. Set PYTHONPATH first:

```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Critical for imports!
```

#### Running the Application

```bash
# Parse knowledge base (converts markdown to JSON)
python -c "from backend_eng.services.knowledge_parser import parse_knowledge_base; parse_knowledge_base()"

# Run the application
python -m backend_eng.api.main

# Or with auto-reload
python -m uvicorn backend_eng.api.main:app --reload --port 8000
```

#### Testing Individual Modules

```bash
# Test parser
python test_parser.py

# Test science module
python -c "from science.agents import TaxConsultationWorkflow; print('Science module OK')"

# Test backend_eng
python -c "from backend_eng.api.main import app; print('Backend eng module OK')"
```

#### Install Dependencies

```bash
# Install both modules
pip install -r science/requirements.txt
pip install -r backend_eng/requirements.txt

# Or install as packages
pip install -e ./science
pip install -e ./backend_eng
```

### Frontend (React + Vite)

```bash
cd frontend

# Development server
npm run dev          # Runs on http://localhost:5173

# Build and validate
npm run build        # TypeScript compilation + Vite build
npm run lint         # ESLint

# Install dependencies
npm install
```

### Docker Development

```bash
# Development with hot reload (auto-parses markdown)
docker-compose -f docker-compose.dev.yml up -d

# Production build
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## Architecture

### Three-Module Structure

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                            │
│                (React + TypeScript)                      │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/SSE
                     ↓
┌─────────────────────────────────────────────────────────┐
│              backend_eng/ (Backend Engineering)          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  FastAPI App (api/main.py)                       │  │
│  │  - Routes, validation, streaming                 │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Services                                         │  │
│  │  - session_service: State conversion             │  │
│  │  - stream_service: SSE streaming                 │  │
│  │  - knowledge_parser: MD → JSON (critical!)       │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Python imports
                     ↓
┌─────────────────────────────────────────────────────────┐
│                science/ (AI/ML Team)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  LangGraph Workflow (agents/workflow.py)         │  │
│  │  IntakeNode → FormsAnalysisNode → CompletionNode│  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  LLM Service (services/llm_service.py)           │  │
│  │  - OpenAI / Gemini configuration                 │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Reads JSON
                     ↓
┌─────────────────────────────────────────────────────────┐
│         backend_eng/knowledge_cache/ (auto-generated)    │
│                    JSON files                            │
│                       ↑                                  │
│                  Parsed from                             │
│                       ↓                                  │
│              tax_team/ (Tax Experts)                     │
│  knowledge_base/                                         │
│  ├── intake/questions.md (18 gating + 9 modules)        │
│  ├── tags/definitions.md (30+ tags)                     │
│  ├── forms/us_forms.md                                   │
│  └── forms/canada_forms.md                               │
│                                                           │
│  (Human-editable markdown, no coding!)                  │
└─────────────────────────────────────────────────────────┘
```

### Team Ownership

| Module | Owner | Responsibilities | Language |
|--------|-------|------------------|----------|
| **science/** | ML Team | AI workflow, LLM prompts, model config | Python |
| **backend_eng/** | Backend Eng | API, orchestration, MD parsing | Python |
| **tax_team/** | Tax Experts | Knowledge content, forms, rules | Markdown |

### LangGraph Workflow (Science Module)

**Workflow:** `IntakeNode` → `FormsAnalysisNode` → `CompletionNode`

- **IntakeNode** (`science/agents/nodes.py:66`): Asks one question at a time using knowledge base, assigns tags
- **FormsAnalysisNode** (`science/agents/nodes.py:344`): Generates form requirements based on assigned tags
- **CompletionNode** (`science/agents/nodes.py:541`): Handles follow-up questions

**Workflow Definition:** `science/agents/workflow.py`
- Built using `StateGraph(TaxConsultationState)`
- Configured with `recursion_limit: 25` (from `science/config.py`)
- Memory persisted via `MemorySaver`
- Thread ID = session ID

**Transition Logic:**
- Stays in intake until ≥2 tags assigned AND ≥6 conversation turns
- Can be forced via `/session/{session_id}/force_final` endpoint
- One question at a time strategy

### State Management

**TaxConsultationState** (`science/agents/state.py`):
- Comprehensive TypedDict with 30+ fields
- Includes: messages, current_phase, assigned_tags, user_profile, knowledge_base context, forms analysis results
- Created via `create_initial_state()` for new sessions

### Tag-Based Knowledge System

**Critical concept:** Tags drive the entire forms recommendation system.

**Knowledge Base Location:**
- **Source (tax team edits)**: `tax_team/knowledge_base/*.md`
- **Parsed cache (science reads)**: `backend_eng/knowledge_cache/*.json`

**Flow:**
1. Tax team edits markdown in `tax_team/`
2. Backend eng parser converts MD → JSON in `knowledge_cache/`
3. Science module reads JSON from cache
4. IntakeNode asks questions from knowledge base
5. Questions have actions like "Add tag `us_person_worldwide_filing`"
6. LLM assigns tags when criteria met
7. FormsAnalysisNode reads tag definitions to determine required forms
8. Each tag specifies forms per jurisdiction (US, Canada, State)

**Example Tag Structure (from markdown):**
```markdown
## us_person_worldwide_filing

**Name**: U.S. person (citizen/green-card holder) - worldwide U.S. filing

**Description**: You are a U.S. citizen...

**Forms:**

### United States
- **Form 1040**: Annual U.S. individual income tax return
- **Form 1116**: Foreign Tax Credit

**Why**: U.S. persons must report worldwide income...
```

### API Endpoints (Backend Eng Module)

**FastAPI Backend** (`backend_eng/api/main.py`):
- `POST /session/create`: Initialize new consultation
- `POST /chat`: Send message (streaming response via SSE)
- `POST /message/edit`: Edit previous message (treated as continuation)
- `POST /session/{id}/force_final`: Force transition to forms analysis
- `GET /session/{id}`: Retrieve session state
- `GET /session/{id}/debug`: Debug workflow state
- `GET /health`: Health check

**Streaming Implementation:**
- Uses `StreamingResponse` with `text/event-stream`
- Character-by-character streaming (configurable delay in `backend_eng/config.py`)
- Final chunk includes `is_final: true` + full case_file state

**State Conversion:** `backend_eng/services/session_service.py`
- Converts LangGraph state → Frontend CaseFile format
- Maps workflow phases → frontend conversation phases
- Transforms message structures

### Markdown Parser (Backend Eng)

**Critical Component:** `backend_eng/services/knowledge_parser.py`

```python
from backend_eng.services.knowledge_parser import parse_knowledge_base

# Parse all markdown files
kb = parse_knowledge_base()

# Output cached to:
# - backend_eng/knowledge_cache/intake/questions.json
# - backend_eng/knowledge_cache/tags/definitions.json
```

**Parser Features:**
- Reads markdown from `tax_team/knowledge_base/`
- Parses structured format (headings, lists, metadata)
- Generates JSON matching original format
- Caches for science module consumption

**Run parser manually:**
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "from backend_eng.services.knowledge_parser import parse_knowledge_base; parse_knowledge_base()"
```

### Frontend Architecture

**Main Hook:** `frontend/src/hooks/useTaxConsultant.ts`
- Session persistence via localStorage
- Handles streaming with async generators
- Optimistic UI updates

**Key Components:**
- `App.tsx`: Main layout
- `ChatMessage.tsx`: Individual message with edit capability
- `CaseSidebar.tsx`: Displays user profile, tags
- `ChatInput.tsx`: Message input with quick replies

## Important Configuration

### AI Model Selection (Science Module)

**File:** `science/config.py:13`

```python
class ScienceConfig:
    AI_MODEL_PROVIDER: str = "openai"  # or "gemini"
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_MODEL: str = "models/gemini-1.5-flash-latest"
    LLM_TEMPERATURE: float = 0.1

    # Workflow settings
    WORKFLOW_RECURSION_LIMIT: int = 25
    MIN_TAGS_FOR_TRANSITION: int = 2
    MIN_CONVERSATION_LENGTH: int = 6
```

### Backend Configuration

**File:** `backend_eng/config.py`

```python
class BackendConfig:
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    STREAMING_CHAR_DELAY: float = 0.01  # Delay per character
```

### API Keys

Set in `.env` file at project root:
```
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## Key Implementation Patterns

### Knowledge Base Updates (Tax Team Workflow)

1. Tax expert edits `tax_team/knowledge_base/*.md`
2. Git commit changes
3. Backend eng runs parser (manual or automated):
   ```bash
   python -c "from backend_eng.services.knowledge_parser import parse_knowledge_base; parse_knowledge_base()"
   ```
4. Cached JSON updated in `backend_eng/knowledge_cache/`
5. Science module reads new JSON on next load
6. No code changes required!

### Science Module Independence

Science module can be tested/run independently:

```python
import asyncio
from science.agents import TaxConsultationWorkflow

async def test():
    workflow = TaxConsultationWorkflow()
    result = await workflow.start_consultation("I'm a US citizen in Canada")
    print(result)

asyncio.run(test())
```

### Adding New Features

**New Tax Situation (Tax Team):**
1. Add question to `tax_team/knowledge_base/intake/questions.md`
2. Add tag to `tax_team/knowledge_base/tags/definitions.md`
3. Run parser
4. Test!

**New AI Behavior (Science Team):**
1. Edit `science/agents/nodes.py` or `science/agents/prompts.py`
2. Test workflow
3. Deploy science module

**New API Endpoint (Backend Eng):**
1. Add route to `backend_eng/api/main.py`
2. Add service in `backend_eng/services/`
3. Update schemas in `backend_eng/models/schemas.py`

## File Structure

### Backend Critical Files

**Science Module:**
- `science/config.py`: AI model configuration
- `science/agents/workflow.py`: LangGraph workflow
- `science/agents/state.py`: State schema
- `science/agents/nodes.py`: Workflow nodes
- `science/agents/prompts.py`: LLM prompts
- `science/services/llm_service.py`: LLM initialization

**Backend Eng Module:**
- `backend_eng/api/main.py`: FastAPI app & endpoints
- `backend_eng/models/schemas.py`: Pydantic models
- `backend_eng/services/session_service.py`: State conversion
- `backend_eng/services/stream_service.py`: SSE streaming
- `backend_eng/services/knowledge_parser.py`: MD → JSON parser
- `backend_eng/utils/validation.py`: Input validation
- `backend_eng/config.py`: Backend configuration

**Tax Team Module:**
- `tax_team/knowledge_base/intake/questions.md`: All intake questions
- `tax_team/knowledge_base/tags/definitions.md`: Tag definitions & forms
- `tax_team/README.md`: Editing guide for tax team

### Frontend Critical Files
- `frontend/src/hooks/useTaxConsultant.ts`: Main state hook
- `frontend/src/api/client.ts`: API client
- `frontend/src/types/index.ts`: TypeScript types
- `frontend/src/App.tsx`: Main component

## Development Notes

### Import Paths

**Always use absolute imports:**

```python
# ✅ Correct
from science.agents import TaxConsultationWorkflow
from backend_eng.models.schemas import ChatRequest
from backend_eng.services.knowledge_parser import parse_knowledge_base

# ❌ Incorrect
from ..science.agents import TaxConsultationWorkflow
from .models.schemas import ChatRequest
```

### PYTHONPATH Required

For local development:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

Or install as packages:
```bash
pip install -e ./science
pip install -e ./backend_eng
```

### Knowledge Base Cache

Science module looks for JSON in:
1. `backend_eng/knowledge_cache/` (parsed cache)
2. `data/knowledge_base/` (fallback to old location)

Always run parser after markdown changes:
```bash
python -c "from backend_eng.services.knowledge_parser import parse_knowledge_base; parse_knowledge_base()"
```

### Testing

**Test parser:**
```bash
python test_parser.py
```

**Test full flow:**
```bash
# Start backend
python -m backend_eng.api.main

# Test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/session/create
```

## Common Tasks

### Adding New Tax Tag

1. Edit `tax_team/knowledge_base/tags/definitions.md`:
```markdown
## new_tax_situation

**Name**: Description of situation

**Description**: Detailed explanation...

**Forms:**

### United States
- **Form XXX**: Description

**Why**: Justification...
```

2. Add question in `tax_team/knowledge_base/intake/questions.md`
3. Run parser: `python -c "from backend_eng.services.knowledge_parser import parse_knowledge_base; parse_knowledge_base()"`
4. Test conversation flow

### Changing LLM Prompts

1. Edit `science/agents/prompts.py`
2. Modify prompt functions
3. Test with: `python -m backend_eng.api.main`
4. Science team owns this file

### Debugging Workflow

Use debug endpoint:
```bash
curl http://localhost:8000/session/{session_id}/debug
```

Returns: current_phase, assigned_tags, message_count, transition flags

### Updating Transition Logic

Edit `science/agents/workflow.py`:
- `should_continue_intake()`: Controls intake → forms_analysis
- Modify thresholds in `science/config.py`

## Dependencies

**Science Module:**
- LangGraph, LangChain (workflow)
- langchain-google-genai (Gemini)
- langchain-openai (OpenAI)
- Pydantic (validation)

**Backend Eng Module:**
- FastAPI (API framework)
- Uvicorn (ASGI server)
- Pydantic (validation)

**Frontend:**
- React 18, TypeScript
- Vite (build tool)
- TanStack Query (data fetching)
- React Markdown (rendering)

## Documentation

- **Architecture**: `backend/RESTRUCTURING_SUMMARY.md`
- **Migration**: `backend/MIGRATION_GUIDE.md`
- **Next Steps**: `backend/NEXT_STEPS.md`
- **Science Module**: `backend/science/README.md`
- **Backend Eng**: `backend/backend_eng/README.md`
- **Tax Team**: `backend/tax_team/README.md`

## Troubleshooting

### "ModuleNotFoundError: No module named 'science'"
Set PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

### "Cannot find knowledge base files"
Run parser: `python -c "from backend_eng.services.knowledge_parser import parse_knowledge_base; parse_knowledge_base()"`

### Parser produces empty JSON
Check markdown format matches templates in `tax_team/README.md`

### Application won't start
1. Check PYTHONPATH is set
2. Verify dependencies installed
3. Run parser first
4. Check logs for detailed errors