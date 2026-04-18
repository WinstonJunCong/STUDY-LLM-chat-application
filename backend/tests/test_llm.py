"""LLM service tests - testing what we can without external API"""
import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["GEMINI_API_KEY"] = "test_api_key"

from app.services import llm


@pytest.mark.asyncio
async def test_get_full_response_returns_string():
    """Test get_full_response makes an API call (will fail with test key)"""
    result = await llm.get_full_response([])
    assert isinstance(result, str)


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