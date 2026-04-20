"""LLM service tests with proper HTTP mocking using respx - llama.cpp version"""
import pytest
import os
import sys
from pathlib import Path

# Set environment BEFORE importing llm
os.environ["LLAMACPP_URL"] = "http://llamacpp:8080"

sys.path.insert(0, str(Path(__file__).parent.parent))

import respx
import httpx
import app.services.llm as llm


@pytest.mark.asyncio
async def test_oom_returns_friendly_message():
    """Test that OOM returns friendly message"""
    with respx.mock:
        respx.post(url__startswith="http://llamacpp:8080/v1/chat").mock(
            return_value=httpx.Response(500, text="error: failed to load model: out of memory")
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "out of memory" in result[0]


@pytest.mark.asyncio
async def test_model_not_found_returns_friendly_message():
    """Test that model not found returns friendly message"""
    with respx.mock:
        respx.post(url__startswith="http://llamacpp:8080/v1/chat").mock(
            return_value=httpx.Response(400, text="error: failed to load model: file not found")
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "not found" in result[0]


@pytest.mark.asyncio
async def test_gpu_error_returns_friendly_message():
    """Test that GPU error returns friendly message"""
    with respx.mock:
        respx.post(url__startswith="http://llamacpp:8080/v1/chat").mock(
            return_value=httpx.Response(500, text="error: CUDA error: no CUDA-capable device")
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "GPU error" in result[0]


@pytest.mark.asyncio
async def test_unknown_error_exposes_code():
    """Test that unknown errors expose the error for debugging"""
    with respx.mock:
        respx.post(url__startswith="http://llamacpp:8080/v1/chat").mock(
            return_value=httpx.Response(500, text="Unknown internal error occurred")
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "500" in result[0]


@pytest.mark.asyncio
async def test_successful_response_streams_tokens():
    """Test that 200 returns streamed tokens"""
    sse_data = (
        'data: {"choices":[{"delta":{"content":"Hello"},"index":0,"finish_reason":null}]}\n\n'
        'data: {"choices":[{"delta":{"content":" world"},"index":0,"finish_reason":null}]}\n\n'
        'data: {"choices":[{"delta":{},"index":0,"finish_reason":"stop"}]}\n\n'
    )
    
    with respx.mock:
        respx.post(url__startswith="http://llamacpp:8080/v1/chat").mock(
            return_value=httpx.Response(200, text=sse_data)
        )
        
        result = []
        async for token in llm.stream_llm_response([{"role": "user", "parts": [{"text": "Hi"}]}]):
            result.append(token)
        
        assert len(result) >= 1
        assert "token" in result[0]
        assert "Hello" in result[0]


def test_llm_module_imports():
    """Test that llm module loads correctly"""
    assert hasattr(llm, 'stream_llm_response')
    assert hasattr(llm, 'generate_with_history')
    assert hasattr(llm, 'get_full_response')
    assert "llamacpp" in llm.LLAMACPP_URL


def test_llm_api_url_uses_correct_endpoint():
    """Test that API URL uses llama.cpp endpoint"""
    assert "/v1/chat/completions" in llm.LLAMACPP_API_URL
    assert "llamacpp" in llm.LLAMACPP_URL