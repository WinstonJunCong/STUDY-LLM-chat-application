"""API route tests"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import database


def test_chat_empty_message_returns_422(test_client):
    """Test that empty message returns 422"""
    response = test_client.post(
        "/api/chat",
        json={"message": ""}
    )
    
    assert response.status_code == 422


def test_chat_whitespace_message_returns_422(test_client):
    """Test that whitespace-only message returns 422"""
    response = test_client.post(
        "/api/chat",
        json={"message": "   "}
    )
    
    assert response.status_code == 422


def test_get_messages_empty(test_client):
    """Test GET /messages returns empty list initially"""
    response = test_client.get("/api/messages")
    
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert data["messages"] == []


def test_get_messages_with_data(test_client):
    """Test GET /messages returns stored messages"""
    database.add_message("user", "Hello")
    database.add_message("assistant", "Hi there")
    
    response = test_client.get("/api/messages")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Hello"
    assert data["messages"][1]["content"] == "Hi there"


def test_reset_clears_conversation(test_client):
    """Test POST /reset clears all messages"""
    database.add_message("user", "Hello")
    database.add_message("assistant", "Hi")
    
    response = test_client.post("/api/reset")
    
    assert response.status_code == 200
    
    messages = database.get_all_messages()
    assert len(messages) == 0


def test_delete_messages(test_client):
    """Test DELETE /messages clears all messages"""
    database.add_message("user", "Test")
    
    response = test_client.delete("/api/messages")
    
    assert response.status_code == 200
    
    messages = database.get_all_messages()
    assert len(messages) == 0