"""Conversation memory system using ChromaDB"""
import uuid
from datetime import datetime
from typing import AsyncGenerator
from . import vector_store

COLLECTION_MEMORY = "memory"


async def add_turn(query: str, response: str):
    """Store a conversation turn (query + response)"""
    doc_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    metadata = {
        "query": query,
        "response": response,
        "timestamp": timestamp
    }
    
    combined_text = f"Query: {query}\nResponse: {response}"
    
    vector_store.add_document(
        collection_name=COLLECTION_MEMORY,
        text=combined_text,
        doc_id=doc_id,
        metadata=metadata
    )


async def retrieve_context(query: str, n_results: int = 3) -> list:
    """Retrieve relevant conversation history for a query"""
    results = vector_store.query_collection(
        collection_name=COLLECTION_MEMORY,
        query_text=query,
        n_results=n_results
    )
    
    context_parts = []
    for r in results:
        meta = r.get("metadata", {})
        context_parts.append({
            "query": meta.get("query", ""),
            "response": meta.get("response", ""),
            "timestamp": meta.get("timestamp", "")
        })
    
    return context_parts


def format_context(contexts: list) -> str:
    """Format retrieved context for LLM prompt"""
    if not contexts:
        return ""
    
    formatted = ["Previous relevant conversations:\n"]
    for i, ctx in enumerate(contexts, 1):
        formatted.append(f"{i}. Q: {ctx['query']}")
        formatted.append(f"   A: {ctx['response']}\n")
    
    return "\n".join(formatted)


async def clear_memory():
    """Clear all conversation memory"""
    vector_store.delete_collection(COLLECTION_MEMORY)