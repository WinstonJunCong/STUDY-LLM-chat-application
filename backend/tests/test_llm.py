"""LLM service tests with proper HTTP mocking using respx - VLLM version"""
import pytest
import os
import sys
from pathlib import Path

# Set environment BEFORE importing llm
os.environ["VLLM_URL"] = "http://vllm:8000"
os.environ["VLLM_MODEL"] = "meta-llama/Llama-3.2-1B-Instruct"

sys.path.insert(0, str(Path(__file__).parent.parent))

import respx
import httpx
import app.services.llm as llm


@pytest.mark.asyncio
async def test_500_returns_server_error():
    """Test that 500 returns server error message"""
    with respx.mock:
        respx.post(url__startswith="http://vllm:8000/v1/chat").mock(
            return_value=httpx.Response(500)
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "not be loaded" in result[0]


@pytest.mark.asyncio
async def test_503_returns_service_unavailable():
    """Test that 503 returns service unavailable message"""
    with respx.mock:
        respx.post(url__startswith="http://vllm:8000/v1/chat").mock(
            return_value=httpx.Response(503)
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "unavailable" in result[0]


@pytest.mark.asyncio
async def test_404_returns_model_not_found():
    """Test that 404 returns model not found message"""
    with respx.mock:
        respx.post(url__startswith="http://vllm:8000/v1/chat").mock(
            return_value=httpx.Response(404)
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "not found" in result[0]


@pytest.mark.asyncio
async def test_cuda_oom_returns_friendly_message():
    """Test that CUDA OOM returns friendly message"""
    with respx.mock:
        respx.post(url__startswith="http://vllm:8000/v1/chat").mock(
            return_value=httpx.Response(507, text="CUDA out of memory. Tried to allocate 2.00 GiB")
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "out of memory" in result[0]


@pytest.mark.asyncio
async def test_unknown_error_exposes_code():
    """Test that unknown errors expose the error code for debugging"""
    with respx.mock:
        respx.post(url__startswith="http://vllm:8000/v1/chat").mock(
            return_value=httpx.Response(520, text="Unknown error from VLLM server")
        )
        
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "520" in result[0]


@pytest.mark.asyncio
async def test_successful_response_streams_tokens():
    """Test that 200 returns streamed tokens"""
    sse_data = (
        'data: {"choices":[{"delta":{"content":"Hello"},"index":0,"finish_reason":null}]}\n\n'
        'data: {"choices":[{"delta":{"content":" world"},"index":0,"finish_reason":null}]}\n\n'
        'data: {"choices":[{"delta":{},"index":0,"finish_reason":"stop"}]}\n\n'
    )
    
    with respx.mock:
        respx.post(url__startswith="http://vllm:8000/v1/chat").mock(
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
    assert llm.VLLM_MODEL == "meta-llama/Llama-3.2-1B-Instruct"


def test_llm_api_url_uses_correct_endpoint():
    """Test that API URL uses VLLM endpoint"""
    assert "/v1/chat/completions" in llm.VLLM_API_URL
    assert "vllm" in llm.VLLM_URL