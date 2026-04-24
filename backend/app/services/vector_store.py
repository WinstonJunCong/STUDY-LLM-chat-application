"""Vector store using ChromaDB with Gemini embeddings"""
import os
import chromadb
from chromadb.config import Settings
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

COLLECTION_KNOWLEDGE = "knowledge"
COLLECTION_MEMORY = "memory"

_client = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        ))
    return _client


def get_embedding(text: str) -> list:
    """Get embedding using Gemini embedding-001"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    
    result = genai.embed_content(
        model="gemini-embedding-001",
        content=text,
        task_type="semantic_retrieval"
    )
    return result["embedding"]


def get_or_create_collection(name: str):
    """Get or create a collection by name"""
    client = get_client()
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name, get_embedding=get_embedding)


def add_document(collection_name: str, text: str, doc_id: str, metadata: dict = None):
    """Add a document to a collection"""
    client = get_client()
    collection = get_or_create_collection(collection_name)
    
    embedding = get_embedding(text)
    metadata = metadata or {"text": text}
    
    collection.add(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata]
    )


def query_collection(collection_name: str, query_text: str, n_results: int = 3) -> list:
    """Query a collection and return results"""
    collection = get_or_create_collection(collection_name)
    
    query_embedding = get_embedding(query_text)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    
    return [
        {"document": doc, "metadata": meta}
        for doc, meta in zip(documents, metadatas)
    ]


def delete_collection(collection_name: str):
    """Delete a collection"""
    client = get_client()
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass


def reset():
    """Reset all collections"""
    global _client
    client = get_client()
    for name in [COLLECTION_KNOWLEDGE, COLLECTION_MEMORY]:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    _client = None