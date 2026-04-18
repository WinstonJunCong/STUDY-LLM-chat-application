"""Shared test fixtures"""
import os
import tempfile

# Set environment variables BEFORE importing app modules
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["DATABASE_PATH"] = temp_db.name
os.environ["GEMINI_API_KEY"] = "test_api_key"

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