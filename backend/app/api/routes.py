"""API routes for chat functionality"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.services import database, llm

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    """Stream LLM response token-by-token using SSE"""
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    database.add_message("user", request.message)

    history = database.get_all_messages()
    history_formatted = [
        {"role": msg["role"], "parts": [{"text": msg["content"]}]}
        for msg in history
    ]

    full_response = ""

    async def token_generator():
        nonlocal full_response
        async for token in llm.stream_llm_response(history_formatted):
            if "error" in token and "API error" in token:
                yield token
                continue
            
            full_response += extract_token_from_sse(token)
            yield token

        if full_response:
            database.add_message("assistant", full_response)
        else:
            database.add_message("assistant", "[No response]")

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked"
        }
    )


def extract_token_from_sse(sse_data: str) -> str:
    """Extract token value from SSE format data: {"token": "..."}"""
    if not sse_data.startswith("data: "):
        return ""
    try:
        import json
        data = json.loads(sse_data[6:])
        return data.get("token", "")
    except:
        return ""


@router.get("/messages")
async def get_messages():
    """Get all conversation messages"""
    messages = database.get_all_messages()
    return {"messages": messages}


@router.delete("/messages")
async def clear_conversation():
    """Clear all conversation history"""
    database.clear_messages()
    return {"message": "Conversation cleared"}


@router.post("/reset")
async def reset_session():
    """Reset session - same as clear conversation"""
    database.clear_messages()
    return {"message": "Session reset successfully"}