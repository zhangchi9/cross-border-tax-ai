from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio
from datetime import datetime

from .models import ChatRequest, EditMessageRequest, CaseFile, MessageRole, ConversationPhase
from .session_manager import session_manager
from langgraph_workflow import TaxConsultationWorkflow
from .config import settings

app = FastAPI(title="Cross-Border Tax Consultant API (LangGraph)")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tax_workflow = TaxConsultationWorkflow()


def json_encoder(obj):
    """Custom JSON encoder for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def workflow_state_to_case_file(workflow_result):
    """Convert workflow result to case_file format expected by frontend"""
    state = workflow_result.get('state', {})

    # Convert workflow messages to frontend ChatMessage format
    messages = []
    for msg in state.get('messages', []):
        messages.append({
            'id': msg.get('id', ''),
            'role': msg.get('role', ''),
            'content': msg.get('content', ''),
            'timestamp': msg.get('timestamp', '')
        })

    # Map workflow phase to frontend conversation phase
    phase_mapping = {
        'intake': 'intake',
        'forms_analysis': 'clarifications',
        'completed': 'final_suggestions'
    }

    conversation_phase = phase_mapping.get(
        workflow_result.get('current_phase', 'intake'),
        'intake'
    )

    case_file = {
        'session_id': workflow_result.get('session_id', ''),
        'user_profile': {
            'countries_involved': state.get('jurisdictions', []),
            'tax_residency_status': state.get('user_profile', {}).get('tax_residency_status'),
            'visa_immigration_status': state.get('user_profile', {}).get('visa_immigration_status'),
            'filing_status': state.get('user_profile', {}).get('filing_status'),
            'tax_year': state.get('user_profile', {}).get('tax_year'),
            'sources_of_income': state.get('income_types', []),
            'foreign_assets': state.get('user_profile', {}).get('foreign_assets', []),
            'credits_deductions': state.get('user_profile', {}).get('credits_deductions', [])
        },
        'jurisdictions': state.get('jurisdictions', []),
        'income_types': state.get('income_types', []),
        'assigned_tags': workflow_result.get('assigned_tags', []),
        'potential_issues': state.get('potential_issues', []),
        'unanswered_questions': [],  # Could be derived from workflow state
        'citations': [],  # Could be derived from workflow state
        'conversation_phase': conversation_phase,
        'messages': messages,
        'created_at': state.get('created_at', ''),
        'updated_at': state.get('updated_at', '')
    }

    return case_file


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/session/create")
async def create_session():
    try:
        result = await tax_workflow.start_consultation("")
        case_file = workflow_state_to_case_file(result)

        return json.loads(json.dumps({
            "session_id": result['session_id'],
            "case_file": case_file
        }, default=json_encoder))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    try:
        # Get the full session state to construct case_file
        debug_info = await tax_workflow.debug_session(session_id)
        if "error" in debug_info:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create a mock workflow result to use the conversion function
        mock_result = {
            'session_id': session_id,
            'current_phase': debug_info.get('current_phase', 'intake'),
            'assigned_tags': debug_info.get('assigned_tags', []),
            'state': debug_info  # The debug info contains the state
        }

        case_file = workflow_state_to_case_file(mock_result)
        return json.loads(json.dumps({"case_file": case_file}, default=json_encoder))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}/workflow_summary")
async def get_workflow_summary(session_id: str):
    """Get the workflow session summary"""
    try:
        summary = await tax_workflow.get_session_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Session not found")
        return json.loads(json.dumps(summary, default=json_encoder))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    # Check for sensitive information
    if _contains_sensitive_info(request.message):
        error_msg = "Please don't share sensitive personal identifiers like SSN, SIN, or full account numbers. I can help with general tax situations without this information."
        return json.loads(json.dumps({"content": error_msg}, default=json_encoder))

    async def generate():
        try:
            # Use LangGraph workflow
            result = await tax_workflow.continue_consultation(request.session_id, request.message)

            if "error" in result:
                # If session not found, try to start a new consultation
                if "Session not found" in result["error"]:
                    result = await tax_workflow.start_consultation(request.message)
                else:
                    yield f"data: {json.dumps({'content': result['error'], 'is_final': True})}\n\n"
                    return

            response_content = result.get("message", "")
            quick_replies = result.get("quick_replies", [])

            # Stream the content character by character
            for char in response_content:
                yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
                await asyncio.sleep(0.01)

            # Send final message with workflow results including case_file
            case_file = workflow_state_to_case_file(result)
            final_response = {
                'is_final': True,
                'session_id': result.get('session_id'),
                'current_phase': result.get('current_phase'),
                'assigned_tags': result.get('assigned_tags', []),
                'quick_replies': quick_replies if quick_replies else None,
                'forms_analysis': result.get('forms_analysis'),
                'transition': result.get('transition', False),
                'case_file': case_file
            }
            yield f"data: {json.dumps(final_response, default=json_encoder)}\n\n"

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            yield f"data: {json.dumps({'content': error_msg, 'is_final': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@app.post("/message/edit")
async def edit_message(request: EditMessageRequest):
    # Check for sensitive information
    if _contains_sensitive_info(request.new_content):
        error_msg = "Please don't share sensitive personal identifiers like SSN, SIN, or full account numbers. I can help with general tax situations without this information."
        return json.loads(json.dumps({
            "content": error_msg,
            "quick_replies": None
        }, default=json_encoder))

    # Note: LangGraph doesn't support message editing in the same way
    # For now, treat this as a new message continuation
    async def generate():
        try:
            result = await tax_workflow.continue_consultation(request.session_id, request.new_content)

            if "error" in result:
                yield f"data: {json.dumps({'content': result['error'], 'is_final': True})}\n\n"
                return

            response_content = result.get("message", "")
            quick_replies = result.get("quick_replies", [])

            # Stream the content character by character
            for char in response_content:
                yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
                await asyncio.sleep(0.01)

            # Send final message with workflow results including case_file
            case_file = workflow_state_to_case_file(result)
            final_response = {
                'is_final': True,
                'session_id': result.get('session_id'),
                'current_phase': result.get('current_phase'),
                'assigned_tags': result.get('assigned_tags', []),
                'quick_replies': quick_replies if quick_replies else None,
                'case_file': case_file
            }
            yield f"data: {json.dumps(final_response, default=json_encoder)}\n\n"

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            yield f"data: {json.dumps({'content': error_msg, 'is_final': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@app.post("/session/{session_id}/force_final")
async def force_final_suggestions(session_id: str):
    try:
        summary = await tax_workflow.get_session_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Session not found")

        if not summary.get('has_sufficient_tags', False):
            raise HTTPException(
                status_code=400,
                detail="Cannot provide final suggestions yet. Please provide more information first."
            )

        async def generate():
            try:
                # Force transition to forms analysis
                result = await tax_workflow.force_forms_analysis(session_id)

                if "error" in result:
                    yield f"data: {json.dumps({'content': result['error'], 'is_final': True})}\n\n"
                    return

                response_content = result.get("message", "")

                # Stream the content
                for char in response_content:
                    yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
                    await asyncio.sleep(0.005)

                # Send final response with forms analysis including case_file
                case_file = workflow_state_to_case_file(result)
                final_response = {
                    'is_final': True,
                    'session_id': result.get('session_id'),
                    'current_phase': result.get('current_phase'),
                    'transition': result.get('transition', True),
                    'forms_analysis': result.get('forms_analysis'),
                    'case_file': case_file
                }
                yield f"data: {json.dumps(final_response, default=json_encoder)}\n\n"

            except Exception as e:
                error_msg = f"Error generating final suggestions: {str(e)}"
                yield f"data: {json.dumps({'content': error_msg, 'is_final': True})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _contains_sensitive_info(message: str) -> bool:
    sensitive_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN format
        r'\b\d{9}\b',              # 9-digit numbers (potential SIN/SSN)
        r'\b\d{3}\s\d{3}\s\d{3}\b', # SIN format with spaces
    ]

    import re
    for pattern in sensitive_patterns:
        if re.search(pattern, message):
            return True
    return False


@app.get("/session/{session_id}/debug")
async def debug_session(session_id: str):
    """Debug endpoint to see internal workflow state"""
    try:
        debug_info = await tax_workflow.debug_session(session_id)
        if "error" in debug_info:
            raise HTTPException(status_code=404, detail=debug_info["error"])
        return debug_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)