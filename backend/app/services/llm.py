"""LLM service for Gemini API with streaming support"""
import os
import json
from typing import AsyncGenerator
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent?alt=sse"


async def stream_llm_response(history: list[dict]) -> AsyncGenerator[str, None]:
    """Stream tokens from Gemini API using SSE"""
    if not GEMINI_API_KEY:
        yield "data: {\"error\": \"GEMINI_API_KEY not set\"}\n\n"
        return

    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": history,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream(
                "POST",
                GEMINI_API_URL,
                headers=headers,
                json=payload,
                params={"key": GEMINI_API_KEY}
            ) as response:
                if response.status_code == 503:
                    yield 'data: {"error": "Service temporarily unavailable. Please try again in a few moments."}\n\n'
                    return
                elif response.status_code == 429:
                    yield 'data: {"error": "Rate limit exceeded. Please wait a moment and try again."}\n\n'
                    return
                elif response.status_code == 403:
                    yield 'data: {"error": "Invalid API key. Please check your API key configuration."}\n\n'
                    return
                elif response.status_code == 400:
                    try:
                        error_body = await response.aread()
                        error_msg = error_body.decode()
                    except:
                        error_msg = "Bad request"
                    yield f'data: {{"error": "Bad request: {error_msg}"}}\n\n'
                    return
                elif response.status_code != 200:
                    try:
                        error_body = await response.aread()
                        error_msg = error_body.decode()
                    except:
                        error_msg = f"HTTP {response.status_code}"
                    yield f'data: {{"error": "API error: {error_msg}"}}\n\n'
                    return

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    # Process all complete events (separated by \n\n)
                    while "\n\n" in buffer:
                        event, buffer = buffer.split("\n\n", 1)
                        for line in event.splitlines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                try:
                                    data = json.loads(data_str)
                                    candidates = data.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        for part in parts:
                                            if "text" in part and part["text"]:
                                                yield f"data: {json.dumps({'token': part['text']})}\n\n"
                                except json.JSONDecodeError:
                                    continue
                    
                    # Process any remaining data in buffer (final chunk without \n\n)
                    if buffer.strip() and not buffer.endswith("\n\n"):
                        if buffer.startswith("data: "):
                            try:
                                data = json.loads(buffer[6:])
                                candidates = data.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        if "text" in part and part["text"]:
                                            yield f"data: {json.dumps({'token': part['text']})}\n\n"
                            except:
                                pass
                        buffer = ""
        except Exception as e:
            yield f'data: {{"error": "{str(e)}"}}\n\n'


async def generate_with_history(history: list[dict]) -> str:
    """Non-streaming LLM response (fallback)"""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not set"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": history,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                GEMINI_API_URL,
                headers=headers,
                json=payload,
                params={"key": GEMINI_API_KEY}
            )
            if response.status_code != 200:
                return f"API error: {response.status_code}"
            
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0].get("content", {})
                parts = content.get("parts", [])
                return "".join(p.get("text", "") for p in parts)
            return "No response"
        except Exception as e:
            return f"Error: {str(e)}"


async def get_full_response(history: list[dict]) -> str:
    """Get full response for database storage"""
    return await generate_with_history(history)