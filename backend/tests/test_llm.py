"""LLM service tests with proper HTTP mocking using respx"""
import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["GEMINI_API_KEY"] = "test_api_key"

import respx
import httpx
from app.services import llm


@pytest.mark.asyncio
async def test_no_api_key_returns_error():
    """Test that empty API key returns an error"""
    import app.services.llm as llm_module
    original_key = llm_module.GEMINI_API_KEY
    llm_module.GEMINI_API_KEY = ""
    
    try:
        result = []
        async for token in llm.stream_llm_response([]):
            result.append(token)
        
        assert len(result) == 1
        assert "error" in result[0]
    finally:
        llm_module.GEMINI_API_KEY = original_key


@respx.mock
@pytest.mark.asyncio
async def test_503_returns_service_unavailable():
    """Test that 503 returns 'Service temporarily unavailable'"""
    mock_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:streamGenerateContent"
    respx.post(mock_url).mock(return_value=httpx.Response(503))
    
    result = []
    async for token in llm.stream_llm_response([]):
        result.append(token)
    
    assert len(result) == 1
    assert "error" in result[0]
    assert "temporarily unavailable" in result[0]


@respx.mock
@pytest.mark.asyncio
async def test_429_returns_rate_limit():
    """Test that 429 returns 'Rate limit exceeded'"""
    mock_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:streamGenerateContent"
    respx.post(mock_url).mock(return_value=httpx.Response(429))
    
    result = []
    async for token in llm.stream_llm_response([]):
        result.append(token)
    
    assert len(result) == 1
    assert "error" in result[0]
    assert "Rate limit" in result[0]


@respx.mock
@pytest.mark.asyncio
async def test_403_returns_invalid_key():
    """Test that 403 returns 'Invalid API key'"""
    mock_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:streamGenerateContent"
    respx.post(mock_url).mock(return_value=httpx.Response(403))
    
    result = []
    async for token in llm.stream_llm_response([]):
        result.append(token)
    
    assert len(result) == 1
    assert "error" in result[0]
    assert "Invalid API key" in result[0]


@respx.mock
@pytest.mark.asyncio
async def test_400_returns_bad_request():
    """Test that 400 returns 'Bad request'"""
    mock_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:streamGenerateContent"
    respx.post(mock_url).mock(return_value=httpx.Response(400, text="Invalid request body"))
    
    result = []
    async for token in llm.stream_llm_response([]):
        result.append(token)
    
    assert len(result) == 1
    assert "error" in result[0]
    assert "Bad request" in result[0]


@respx.mock
@pytest.mark.asyncio
async def test_successful_response_streams_tokens():
    """Test that 200 returns streamed tokens"""
    sse_data = (
        'data: {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]}\n\n'
        'data: {"candidates": [{"content": {"parts": [{"text": " world"}]}}]}\n\n'
    )
    
    mock_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:streamGenerateContent"
    respx.post(mock_url).mock(return_value=httpx.Response(200, text=sse_data))
    
    result = []
    async for token in llm.stream_llm_response([]):
        result.append(token)
    
    assert len(result) == 2
    assert "token" in result[0]
    assert "Hello" in result[0]
    assert " world" in result[1]


def test_llm_module_imports():
    """Test that llm module loads correctly"""
    assert hasattr(llm, 'stream_llm_response')
    assert hasattr(llm, 'generate_with_history')
    assert hasattr(llm, 'get_full_response')
    assert llm.GEMINI_MODEL == "gemini-3.1-flash-lite-preview"


def test_llm_api_url_uses_correct_model():
    """Test that API URL uses the correct model"""
    assert "gemini-3.1-flash-lite-preview" in llm.GEMINI_API_URL
    assert "streamGenerateContent" in llm.GEMINI_API_URL
    assert "alt=sse" in llm.GEMINI_API_URL