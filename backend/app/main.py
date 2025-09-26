from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio
from datetime import datetime

from .models import ChatRequest, CaseFile, MessageRole, ConversationPhase
from .session_manager import session_manager
from .tax_consultant import TaxConsultant
from .config import settings

app = FastAPI(title="Cross-Border Tax Consultant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tax_consultant = TaxConsultant()


def json_encoder(obj):
    """Custom JSON encoder for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/session/create")
async def create_session():
    session_id = session_manager.create_session()
    case_file = session_manager.get_session(session_id)
    return json.loads(json.dumps({"session_id": session_id, "case_file": case_file.dict()}, default=json_encoder))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    case_file = session_manager.get_session(session_id)
    if not case_file:
        raise HTTPException(status_code=404, detail="Session not found")
    return json.loads(json.dumps({"case_file": case_file.dict()}, default=json_encoder))


@app.post("/chat")
async def chat(request: ChatRequest):
    case_file = session_manager.get_session(request.session_id)
    if not case_file:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check for sensitive information
    if _contains_sensitive_info(request.message):
        error_msg = "Please don't share sensitive personal identifiers like SSN, SIN, or full account numbers. I can help with general tax situations without this information."
        session_manager.add_message(request.session_id, MessageRole.ASSISTANT, error_msg)
        return json.loads(json.dumps({"content": error_msg, "case_file": case_file.dict()}, default=json_encoder))

    # Add user message to case file
    session_manager.add_message(request.session_id, MessageRole.USER, request.message)

    async def generate():
        try:
            full_response = ""
            quick_replies = []

            async for chunk_content, chunk_quick_replies in tax_consultant.generate_response(case_file, request.message):
                if chunk_content:
                    full_response = chunk_content  # This is already the clean content
                    # Capture quick_replies when they come in
                    if chunk_quick_replies:
                        quick_replies = chunk_quick_replies

                    # Stream the clean content character by character for typing effect
                    for char in chunk_content:
                        yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
                        await asyncio.sleep(0.01)

            # Update case file with complete response
            updated_case_file = tax_consultant.update_case_file(case_file, request.message, full_response)
            session_manager.add_message(request.session_id, MessageRole.ASSISTANT, full_response)
            session_manager.update_session(request.session_id, updated_case_file)

            # Send final message with updated case file and quick_replies
            final_response = {
                'content': '',
                'is_final': True,
                'case_file': updated_case_file.dict(),
                'quick_replies': quick_replies if quick_replies else None
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
    case_file = session_manager.get_session(session_id)
    if not case_file:
        raise HTTPException(status_code=404, detail="Session not found")

    if not tax_consultant.can_provide_final_suggestions(case_file):
        raise HTTPException(
            status_code=400,
            detail="Cannot provide final suggestions yet. Please provide more information first."
        )

    # Force phase to final suggestions
    case_file.conversation_phase = ConversationPhase.FINAL_SUGGESTIONS
    session_manager.update_session(session_id, case_file)

    # Generate final suggestions
    final_prompt = "Based on all the information gathered, please provide your final comprehensive tax suggestions in a structured format."

    async def generate():
        try:
            full_response = ""
            async for chunk in tax_consultant.generate_response(case_file, final_prompt):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk, 'is_final': False})}\n\n"
                await asyncio.sleep(0.01)

            # Add final response to case file
            session_manager.add_message(session_id, MessageRole.ASSISTANT, full_response)
            updated_case_file = session_manager.get_session(session_id)

            yield f"data: {json.dumps({'content': '', 'is_final': True, 'case_file': updated_case_file.dict()}, default=json_encoder)}\n\n"

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)