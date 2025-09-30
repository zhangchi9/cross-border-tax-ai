"""
FastAPI Main Application

Orchestrates between frontend and science team's AI workflow.

Owner: Backend Engineering Team
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Science team imports
from science.agents import TaxConsultationWorkflow

# Backend eng imports
from backend_eng.config import backend_config
from backend_eng.models.schemas import ChatRequest, EditMessageRequest
from backend_eng.services.session_service import workflow_state_to_case_file
from backend_eng.services.stream_service import stream_chat_response, stream_force_final_response
from backend_eng.utils.validation import contains_sensitive_info, get_sensitive_info_error_message

# Initialize FastAPI app
app = FastAPI(
    title=backend_config.API_TITLE,
    version=backend_config.API_VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=backend_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize science team's workflow
tax_workflow = TaxConsultationWorkflow()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "backend_eng"}


@app.post("/session/create")
async def create_session():
    """Create a new consultation session"""
    try:
        # Call science team's workflow
        result = await tax_workflow.start_consultation("")

        # Convert to frontend format
        case_file = workflow_state_to_case_file(result)

        return {
            "session_id": result['session_id'],
            "case_file": case_file.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    try:
        # Get debug info from science team
        debug_info = await tax_workflow.debug_session(session_id)
        if "error" in debug_info:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create a mock workflow result for conversion
        mock_result = {
            'session_id': session_id,
            'current_phase': debug_info.get('current_phase', 'intake'),
            'assigned_tags': debug_info.get('assigned_tags', []),
            'state': debug_info
        }

        case_file = workflow_state_to_case_file(mock_result)
        return {"case_file": case_file.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}/workflow_summary")
async def get_workflow_summary(session_id: str):
    """Get workflow session summary"""
    try:
        summary = await tax_workflow.get_session_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Session not found")
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with streaming response"""

    # Check for sensitive information
    if contains_sensitive_info(request.message):
        error_msg = get_sensitive_info_error_message()
        return {"content": error_msg}

    async def generate():
        try:
            # Call science team's workflow
            result = await tax_workflow.continue_consultation(request.session_id, request.message)

            if "error" in result:
                # If session not found, try to start a new consultation
                if "Session not found" in result["error"]:
                    result = await tax_workflow.start_consultation(request.message)
                else:
                    yield f"data: {{'content': '{result['error']}', 'is_final': true}}\n\n"
                    return

            response_content = result.get("message", "")

            # Convert to frontend format
            case_file = workflow_state_to_case_file(result)

            # Stream response
            async for chunk in stream_chat_response(
                response_content,
                result,
                case_file.model_dump()
            ):
                yield chunk

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            yield f"data: {{'content': '{error_msg}', 'is_final': true}}\n\n"

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
    """Edit a previous message (currently implemented as continuation)"""

    # Check for sensitive information
    if contains_sensitive_info(request.new_content):
        error_msg = get_sensitive_info_error_message()
        return {"content": error_msg, "quick_replies": None}

    async def generate():
        try:
            # Note: LangGraph doesn't support true message editing
            # Treating as continuation for now
            result = await tax_workflow.continue_consultation(request.session_id, request.new_content)

            if "error" in result:
                yield f"data: {{'content': '{result['error']}', 'is_final': true}}\n\n"
                return

            response_content = result.get("message", "")

            # Convert to frontend format
            case_file = workflow_state_to_case_file(result)

            # Stream response
            async for chunk in stream_chat_response(
                response_content,
                result,
                case_file.model_dump()
            ):
                yield chunk

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            yield f"data: {{'content': '{error_msg}', 'is_final': true}}\n\n"

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
    """Force transition to final suggestions"""
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
                # Force transition via science team
                result = await tax_workflow.force_forms_analysis(session_id)

                if "error" in result:
                    yield f"data: {{'content': '{result['error']}', 'is_final': true}}\n\n"
                    return

                response_content = result.get("message", "")

                # Convert to frontend format
                case_file = workflow_state_to_case_file(result)

                # Stream response
                async for chunk in stream_force_final_response(
                    response_content,
                    result,
                    case_file.model_dump()
                ):
                    yield chunk

            except Exception as e:
                error_msg = f"Error generating final suggestions: {str(e)}"
                yield f"data: {{'content': '{error_msg}', 'is_final': true}}\n\n"

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