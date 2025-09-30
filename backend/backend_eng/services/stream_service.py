"""
Stream Service

Handles streaming responses for real-time UI updates.

Owner: Backend Engineering Team
"""
import json
import asyncio
from typing import AsyncGenerator
from datetime import datetime

from backend_eng.config import backend_config


def json_encoder(obj):
    """Custom JSON encoder for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


async def stream_chat_response(
    response_content: str,
    result: dict,
    case_file: dict,
    delay: float = None
) -> AsyncGenerator[str, None]:
    """
    Stream chat response character by character

    Args:
        response_content: Full response text
        result: Workflow result dictionary
        case_file: Case file dictionary
        delay: Delay between characters (uses config default if None)

    Yields:
        Server-sent event strings
    """
    if delay is None:
        delay = backend_config.STREAMING_CHAR_DELAY

    # Stream the content character by character
    for char in response_content:
        yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
        await asyncio.sleep(delay)

    # Send final message with workflow results including case_file
    final_response = {
        'is_final': True,
        'session_id': result.get('session_id'),
        'current_phase': result.get('current_phase'),
        'assigned_tags': result.get('assigned_tags', []),
        'quick_replies': result.get('quick_replies') if result.get('quick_replies') else None,
        'forms_analysis': result.get('forms_analysis'),
        'transition': result.get('transition', False),
        'case_file': case_file
    }
    yield f"data: {json.dumps(final_response, default=json_encoder)}\n\n"


async def stream_force_final_response(
    response_content: str,
    result: dict,
    case_file: dict
) -> AsyncGenerator[str, None]:
    """
    Stream force final response (faster than normal chat)

    Args:
        response_content: Full response text
        result: Workflow result dictionary
        case_file: Case file dictionary

    Yields:
        Server-sent event strings
    """
    # Stream the content with faster delay
    for char in response_content:
        yield f"data: {json.dumps({'content': char, 'is_final': False})}\n\n"
        await asyncio.sleep(backend_config.STREAMING_FORCE_FINAL_DELAY)

    # Send final response with forms analysis
    final_response = {
        'is_final': True,
        'session_id': result.get('session_id'),
        'current_phase': result.get('current_phase'),
        'transition': result.get('transition', True),
        'forms_analysis': result.get('forms_analysis'),
        'case_file': case_file
    }
    yield f"data: {json.dumps(final_response, default=json_encoder)}\n\n"