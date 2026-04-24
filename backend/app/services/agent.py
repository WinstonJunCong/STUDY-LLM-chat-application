"""Agentic AI system - main agent loop"""
from typing import AsyncGenerator
from . import llm
from . import memory
from . import knowledge_base


async def run_agent(query: str, history: list[dict] = None) -> AsyncGenerator[str, None]:
    """Main agent loop: perception → retrieval → reasoning → response
    
    Per requirements:
    - perception: receives user query
    - retrieval: searches vector database (knowledge + memory)
    - reasoning: LLM generates response with context
    - response: streams back to user
    """
    history = history or []
    
    full_response = ""
    
    if history:
        history = history + [{"role": "user", "parts": [{"text": query}]}]
    
    async for token in llm.stream_llm_response(history, use_rag=True):
        if token.startswith("data: "):
            try:
                import json
                data_str = token[6:]
                data = json.loads(data_str)
                if "token" in data:
                    full_response += data["token"]
                    yield token
            except:
                yield token
        else:
            yield token
    
    await memory.add_turn(query, full_response)


async def run_agent_simple(query: str) -> str:
    """Simple synchronous agent for non-streaming use"""
    history = [{"role": "user", "parts": [{"text": query}]}]
    
    response = await llm.generate_with_history(history, use_rag=True)
    
    await memory.add_turn(query, response)
    
    return response


async def add_to_knowledge(text: str, source: str, category: str = None):
    """Add knowledge to the knowledge base"""
    await knowledge_base.add_knowledge(text, source, category)


async def get_conversation_context(query: str, n: int = 3) -> list:
    """Get conversation context for a query"""
    return await memory.retrieve_context(query, n)


async def get_knowledge_context(query: str, n: int = 3) -> list:
    """Get knowledge context for a query"""
    return await knowledge_base.retrieve_knowledge(query, n)


def format_rag_context(knowledge: list, memory: list) -> str:
    """Format combined RAG context for display"""
    parts = []
    
    if knowledge:
        parts.append("=== Knowledge ===")
        for i, item in enumerate(knowledge, 1):
            parts.append(f"{i}. {item['text']} (Source: {item['source']})")
    
    if memory:
        parts.append("\n=== Recent Conversations ===")
        for i, item in enumerate(memory, 1):
            parts.append(f"{i}. Q: {item['query']}")
            parts.append(f"   A: {item['response'][:100]}...")
    
    return "\n".join(parts) if parts else "No context found"