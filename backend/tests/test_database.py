"""Database service tests"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import database


def test_add_message():
    """Test adding a message to database"""
    msg_id = database.add_message("user", "Hello")
    
    assert msg_id is not None
    assert msg_id > 0
    
    messages = database.get_all_messages()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"


def test_add_multiple_messages():
    """Test adding multiple messages preserves order"""
    database.add_message("user", "First")
    database.add_message("assistant", "Second")
    database.add_message("user", "Third")
    
    messages = database.get_all_messages()
    
    assert len(messages) == 3
    assert messages[0]["content"] == "First"
    assert messages[1]["content"] == "Second"
    assert messages[2]["content"] == "Third"


def test_get_all_messages_returns_dict():
    """Test that get_all_messages returns dict with expected keys"""
    database.add_message("user", "Test message")
    
    messages = database.get_all_messages()
    
    assert len(messages) == 1
    assert "id" in messages[0]
    assert "role" in messages[0]
    assert "content" in messages[0]
    assert "timestamp" in messages[0]


def test_clear_messages():
    """Test clearing all messages"""
    database.add_message("user", "Test")
    database.add_message("assistant", "Response")
    
    messages = database.get_all_messages()
    assert len(messages) == 2
    
    database.clear_messages()
    
    messages = database.get_all_messages()
    assert len(messages) == 0


def test_message_roles():
    """Test that user and assistant roles are stored correctly"""
    database.add_message("user", "User message")
    database.add_message("assistant", "Assistant message")
    
    messages = database.get_all_messages()
    
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"