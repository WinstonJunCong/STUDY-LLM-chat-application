"""Shared test fixtures"""
import os
import tempfile

# Set environment variables BEFORE importing app modules
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["DATABASE_PATH"] = temp_db.name
os.environ["VLLM_URL"] = "http://vllm:8000"
os.environ["VLLM_MODEL"] = "meta-llama/Llama-3.2-1B-Instruct"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app
import app.services.database as database

database.init_database()


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test"""
    try:
        database.clear_messages()
    except:
        pass
    yield


@pytest.fixture
def test_client():
    """FastAPI test client"""
    return TestClient(app)