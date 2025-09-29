"""
Updated main.py to use the agentic framework instead of LLM-based consultant
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio
from datetime import datetime

from .models import ChatRequest, EditMessageRequest, CaseFile, MessageRole, ConversationPhase
from .session_manager import session_manager
from .agentic_consultant import AgenticTaxConsultant
from .utils import contains_sensitive_info, get_sensitive_info_error_message
from .config import settings

app = FastAPI(title="Cross-Border Tax Consultant API (Agentic)")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agentic consultant
tax_consultant = AgenticTaxConsultant()


def json_encoder(obj):
    """Custom JSON encoder for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "agentic"}


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


@app.get("/session/{session_id}/agent_summary")
async def get_agent_summary(session_id: str):
    """Get the agent session summary"""
    case_file = session_manager.get_session(session_id)
    if not case_file:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = tax_consultant.get_agent_session_summary(case_file)
    if not summary:
        return {"message": "No agent session found"}

    return json.loads(json.dumps(summary, default=json_encoder))


@app.post("/chat")
async def chat(request: ChatRequest):
    case_file = session_manager.get_session(request.session_id)
    if not case_file:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check for sensitive information
    if contains_sensitive_info(request.message):
        error_msg = get_sensitive_info_error_message()
        session_manager.add_message(request.session_id, MessageRole.ASSISTANT, error_msg)
        return json.loads(json.dumps({"content": error_msg, "case_file": case_file.dict()}, default=json_encoder))

    # Add user message to case file
    session_manager.add_message(request.session_id, MessageRole.USER, request.message)

    async def generate():
        try:
            full_response = ""
            quick_replies = []

            # Generate response using agentic consultant
            async for chunk_content, chunk_quick_replies in tax_consultant.generate_response(case_file, request.message):
                if chunk_content:
                    full_response = chunk_content
                    if chunk_quick_replies:
                        quick_replies = chunk_quick_replies

                    # Stream the content character by character for typing effect
                    for char in chunk_content:
                        yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
                        await asyncio.sleep(0.005)  # Slightly faster than before

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


@app.post("/message/edit")
async def edit_message(request: EditMessageRequest):
    # Edit the message and truncate conversation
    case_file = session_manager.edit_message_and_truncate(
        request.session_id,
        request.message_id,
        request.new_content
    )

    if not case_file:
        raise HTTPException(status_code=404, detail="Session or message not found")

    # Check for sensitive information
    if contains_sensitive_info(request.new_content):
        error_msg = get_sensitive_info_error_message()
        session_manager.add_message(request.session_id, MessageRole.ASSISTANT, error_msg)
        return json.loads(json.dumps({
            "content": error_msg,
            "case_file": case_file.dict(),
            "quick_replies": None
        }, default=json_encoder))

    # Generate new response based on the edited conversation
    async def generate():
        try:
            full_response = ""
            quick_replies = []

            async for chunk_content, chunk_quick_replies in tax_consultant.generate_response(case_file, request.new_content):
                if chunk_content:
                    full_response = chunk_content
                    if chunk_quick_replies:
                        quick_replies = chunk_quick_replies

                    # Stream the content character by character for typing effect
                    for char in chunk_content:
                        yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
                        await asyncio.sleep(0.005)

            # Update case file with complete response
            updated_case_file = tax_consultant.update_case_file(case_file, request.new_content, full_response)
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

    # Get agent session summary for final suggestions
    agent_summary = tax_consultant.get_agent_session_summary(case_file)

    if not agent_summary or not agent_summary.get("forms_analysis_completed"):
        raise HTTPException(
            status_code=400,
            detail="Agent analysis not complete. Please continue the conversation first."
        )

    # Force phase to final suggestions
    case_file.conversation_phase = ConversationPhase.FINAL_SUGGESTIONS
    session_manager.update_session(session_id, case_file)

    async def generate():
        try:
            full_response = ""

            # Generate final response using force_final_suggestions
            async for content, _ in tax_consultant.force_final_suggestions(case_file):
                full_response = content

                # Stream the content
                for char in content:
                    yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
                    await asyncio.sleep(0.005)

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


@app.get("/session/{session_id}/debug")
async def debug_session(session_id: str):
    """Debug endpoint to see internal agent state"""
    case_file = session_manager.get_session(session_id)
    if not case_file:
        raise HTTPException(status_code=404, detail="Session not found")

    agent_summary = tax_consultant.get_agent_session_summary(case_file)

    return {
        "case_file_phase": case_file.conversation_phase,
        "case_file_countries": case_file.user_profile.countries_involved,
        "case_file_income": case_file.user_profile.sources_of_income,
        "case_file_assets": case_file.user_profile.foreign_assets,
        "agent_summary": agent_summary,
        "message_count": len(case_file.messages),
        "can_provide_final": tax_consultant.can_provide_final_suggestions(case_file)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)