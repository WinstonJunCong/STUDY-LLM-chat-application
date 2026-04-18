"""Database service for SQLite operations"""
import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/chat.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    Path("/app/data").mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_message(role: str, content: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_messages (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, datetime.now())
    )
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return message_id


def get_all_messages() -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, role, content, timestamp FROM chat_messages ORDER BY timestamp ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]


def clear_messages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages")
    conn.commit()
    conn.close()