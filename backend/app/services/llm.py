"""LLM service for VLLM (OpenAI-compatible API) with streaming support"""
import os
import json
from typing import AsyncGenerator
import httpx

VLLM_URL = os.getenv("VLLM_URL", "http://vllm:8000")
VLLM_MODEL = os.getenv("VLLM_MODEL", "meta-llama/Llama-3.2-1B-Instruct")
VLLM_API_URL = f"{VLLM_URL}/v1/chat/completions"


async def stream_llm_response(history: list[dict]) -> AsyncGenerator[str, None]:
    """Stream tokens from VLLM using OpenAI-compatible SSE"""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Convert history to OpenAI format if needed
    # VLLM expects: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    messages = []
    for msg in history:
        role = msg.get("role", "user")
        if "parts" in msg:
            content = "".join(p.get("text", "") for p in msg["parts"])
        else:
            content = msg.get("content", "")
        messages.append({"role": role, "content": content})
    
    payload = {
        "model": VLLM_MODEL,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 2048
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "POST",
                VLLM_API_URL,
                headers=headers,
                json=payload
            ) as response:
                if response.status_code == 500:
                    yield 'data: {"error": "Server error. Model may not be loaded yet, please try again."}\n\n'
                    return
                elif response.status_code == 503:
                    yield 'data: {"error": "Service unavailable. Please try again later."}\n\n'
                    return
                elif response.status_code == 404:
                    yield 'data: {"error": "Model not found. Please check VLLM_MODEL configuration."}\n\n'
                    return
                elif response.status_code != 200:
                    try:
                        error_body = await response.aread()
                        error_msg = error_body.decode('utf-8')
                    except:
                        error_msg = f"HTTP {response.status_code}"
                    
                    # Check for CUDA-specific errors
                    if "CUDA" in error_msg or "out of memory" in error_msg.lower():
                        yield 'data: {"error": "GPU out of memory. Try a smaller model or reduce batch size."}\n\n'
                    elif "CUDA" in error_msg:
                        yield f'data: {{"error": "CUDA error: {error_msg[:200]}"}}\n\n'
                    else:
                        # Unknown error - expose for debugging
                        yield f'data: {{"error": "Error {response.status_code}: {error_msg[:300]}"}}\n\n'
                    return

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    # Process all complete lines (separated by \n)
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                continue
                            try:
                                data = json.loads(data_str)
                                # VLLM/OpenAI streaming format
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield f"data: {json.dumps({'token': content})}\n\n"
                            except json.JSONDecodeError:
                                continue
                        
                        # Handle remaining buffer for final chunk
                        if not buffer and line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield f"data: {json.dumps({'token': content})}\n\n"
                            except:
                                pass
        except httpx.TimeoutException:
            yield 'data: {"error": "Request timed out. The model may be slow to respond."}\n\n'
        except Exception as e:
            yield f'data: {{"error": "{str(e)}"}}\n\n'


async def generate_with_history(history: list[dict]) -> str:
    """Non-streaming LLM response (fallback)"""
    headers = {"Content-Type": "application/json"}
    
    # Convert history to OpenAI format
    messages = []
    for msg in history:
        role = msg.get("role", "user")
        if "parts" in msg:
            content = "".join(p.get("text", "") for p in msg["parts"])
        else:
            content = msg.get("content", "")
        messages.append({"role": role, "content": content})
    
    payload = {
        "model": VLLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                VLLM_API_URL,
                headers=headers,
                json=payload
            )
            if response.status_code != 200:
                return f"API error: {response.status_code}"
            
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return "No response"
        except Exception as e:
            return f"Error: {str(e)}"


async def get_full_response(history: list[dict]) -> str:
    """Get full response for database storage"""
    return await generate_with_history(history)