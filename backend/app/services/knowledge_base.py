"""Knowledge base interface - documents managed separately"""
from typing import Optional
from . import vector_store

COLLECTION_KNOWLEDGE = "knowledge"

METADATA_KNOWLEDGE = "knowledge_base"


async def add_knowledge(text: str, source: str, category: Optional[str] = None):
    """Add a piece of knowledge to the knowledge base"""
    import uuid
    
    doc_id = str(uuid.uuid4())
    metadata = {
        "text": text,
        "source": source,
        "category": category or "general",
        "type": METADATA_KNOWLEDGE
    }
    
    vector_store.add_document(
        collection_name=COLLECTION_KNOWLEDGE,
        text=text,
        doc_id=doc_id,
        metadata=metadata
    )


async def retrieve_knowledge(query: str, n_results: int = 5) -> list:
    """Retrieve relevant knowledge for a query"""
    results = vector_store.query_collection(
        collection_name=COLLECTION_KNOWLEDGE,
        query_text=query,
        n_results=n_results
    )
    
    knowledge = []
    for r in results:
        meta = r.get("metadata", {})
        if meta.get("type") == METADATA_KNOWLEDGE:
            knowledge.append({
                "text": meta.get("text", ""),
                "source": meta.get("source", ""),
                "category": meta.get("category", "")
            })
    
    return knowledge


def format_knowledge(knowledge: list) -> str:
    """Format retrieved knowledge for LLM prompt"""
    if not knowledge:
        return ""
    
    formatted = ["Relevant knowledge:\n"]
    for i, item in enumerate(knowledge, 1):
        source = item.get("source", "Unknown")
        category = item.get("category", "")
        prefix = f"{i}. [{category}]" if category else f"{i}."
        formatted.append(f"{prefix} {item['text']} (Source: {source})")
    
    return "\n".join(formatted)


async def clear_knowledge():
    """Clear knowledge base"""
    vector_store.delete_collection(COLLECTION_KNOWLEDGE)