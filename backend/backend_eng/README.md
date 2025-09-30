# Backend Engineering Module

## Owner
**Backend Engineering Team**

## Purpose
This module orchestrates between the frontend and the science team's AI workflow. It provides RESTful API endpoints, manages sessions, handles streaming responses, and converts between data formats.

## Architecture

```
backend_eng/
├── api/
│   └── main.py                 # FastAPI application & endpoints
├── models/
│   └── schemas.py              # Pydantic request/response models
├── services/
│   ├── session_service.py      # State conversion & session mgmt
│   ├── stream_service.py       # Streaming response handling
│   └── knowledge_parser.py     # (TODO) MD → JSON parser
├── utils/
│   └── validation.py           # Input validation & security
└── config.py                   # Backend configuration
```

## Key Responsibilities

### 1. API Endpoints
- `POST /session/create` - Initialize new consultation
- `POST /chat` - Send message (streaming)
- `POST /message/edit` - Edit previous message
- `POST /session/{id}/force_final` - Force final suggestions
- `GET /session/{id}` - Get session details
- `GET /health` - Health check

### 2. Orchestration
- Call science team's `TaxConsultationWorkflow`
- Convert workflow state → frontend `CaseFile` format
- Handle errors and fallbacks
- Manage streaming responses

### 3. Security & Validation
- Detect sensitive information (SSN, SIN, passport numbers)
- Input sanitization
- CORS configuration

### 4. Knowledge Base Integration (TODO)
- Parse markdown files from `tax_team/` module
- Cache parsed JSON for science team consumption
- Watch for changes and regenerate cache

## Running the API

### Development
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m backend_eng.api.main
```

### With Uvicorn
```bash
uvicorn backend_eng.api.main:app --reload --port 8000
```

### Docker
```bash
docker-compose up -d
```

## Configuration

Edit `config.py`:

```python
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
STREAMING_CHAR_DELAY = 0.01  # Delay per character
STREAMING_FORCE_FINAL_DELAY = 0.005  # Faster for force final
```

## Integration Points

### With Science Team
```python
from science.agents import TaxConsultationWorkflow

workflow = TaxConsultationWorkflow()
result = await workflow.continue_consultation(session_id, message)
```

### With Frontend
All endpoints return consistent JSON/streaming formats defined in `models/schemas.py`.

## Data Flow

```
Frontend Request
    ↓
Backend Eng API (validate, check sensitive info)
    ↓
Science Team Workflow (LangGraph processing)
    ↓
Backend Eng Services (convert format, stream response)
    ↓
Frontend (real-time UI updates)
```

## State Conversion

The key conversion function (`session_service.py`):

```python
workflow_result = {
    'session_id': '123',
    'current_phase': 'intake',
    'assigned_tags': ['tag1', 'tag2'],
    'state': {
        'messages': [...],
        'jurisdictions': [...],
        # ... workflow state
    }
}

case_file = workflow_state_to_case_file(workflow_result)
# Returns CaseFile object compatible with frontend
```

## Streaming Implementation

Character-by-character streaming for better UX:

```python
async for chunk in stream_chat_response(response_text, result, case_file):
    yield chunk  # Server-sent events format
```

## TODO: Knowledge Base Parser

Create `services/knowledge_parser.py`:

```python
def parse_tax_team_markdown() -> dict:
    """
    Parse tax_team/*.md files into JSON format
    for science team consumption
    """
    # Read markdown files
    # Parse structured format
    # Generate JSON cache
    # Return parsed knowledge base
```

## Development Tasks

- [ ] Implement markdown parser for tax team content
- [ ] Add knowledge base file watcher
- [ ] Add caching layer for parsed content
- [ ] Add API rate limiting
- [ ] Add request logging/metrics
- [ ] Add session persistence (database)
- [ ] Improve error handling

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/session/create

# Send message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xxx", "message": "I need help with taxes"}'
```

## Deployment

This module is the main entry point for the application:

```bash
uvicorn backend_eng.api.main:app --host 0.0.0.0 --port 8000
```

## Responsibilities

✅ **Backend Eng Team Owns:**
- FastAPI endpoints and routing
- Request/response formats
- Session management
- State conversion (workflow ↔ frontend)
- Streaming implementation
- Input validation and security
- Knowledge base parsing

❌ **Backend Eng Does NOT Own:**
- AI workflow logic (science team)
- LLM prompts (science team)
- Knowledge base content (tax team)
- Frontend code

## Performance Considerations

- Streaming reduces perceived latency
- Character delay can be configured per endpoint
- Consider adding Redis for session caching
- Monitor API response times
- Add request queuing for high load