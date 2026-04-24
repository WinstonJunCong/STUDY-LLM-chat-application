"""Knowledge base seeder - populate with sample ML/AI knowledge"""
from app.services import knowledge_base

SAMPLE_KNOWLEDGE = [
    {
        "text": "Supervised learning is a type of machine learning where the model is trained on labeled data. The algorithm learns from input-output pairs to predict outputs for new, unseen inputs. Examples include classification and regression tasks.",
        "source": "ML Basics",
        "category": "supervised"
    },
    {
        "text": "Unsupervised learning is a type of machine learning where the model is trained on unlabeled data. The algorithm learns patterns and structures from the data without explicit labels. Examples include clustering and dimensionality reduction.",
        "source": "ML Basics", 
        "category": "unsupervised"
    },
    {
        "text": "Reinforcement learning is a type of machine learning where an agent learns to make decisions by taking actions in an environment to maximize a reward. The agent learns through trial and error, receiving feedback in the form of rewards or penalties.",
        "source": "ML Basics",
        "category": "reinforcement"
    },
    {
        "text": "Transfer learning is a machine learning technique where a model trained on one task is repurposed for a related task. This reduces the need for large labeled datasets and training time.",
        "source": "DL Concepts",
        "category": "deep_learning"
    },
    {
        "text": "Fine-tuning is the process of taking a pre-trained model and continuing training on a new dataset to adapt it to a specific task. This is common in NLP with models like BERT and GPT.",
        "source": "DL Concepts",
        "category": "deep_learning"
    },
    {
        "text": "Retrieval-Augmented Generation (RAG) is a technique that enhances LLM responses by retrieving relevant information from a knowledge base and including it in the prompt. This helps the model provide accurate, up-to-date answers.",
        "source": "AI Concepts",
        "category": "rag"
    },
    {
        "text": "Vector databases store embeddings (vector representations of text) and enable semantic search. They are used in RAG systems to retrieve relevant context based on query similarity.",
        "source": "AI Concepts",
        "category": "databases"
    },
    {
        "text": "Embeddings are dense vector representations of text, images, or other data that capture semantic meaning. They enable similarity search and are used in retrieval systems.",
        "source": "AI Concepts",
        "category": "embeddings"
    },
    {
        "text": "Prompt engineering is the practice of designing effective prompts for LLMs to get desired outputs. Techniques include few-shot learning, chain-of-thought reasoning, and role prompting.",
        "source": "AI Concepts",
        "category": "prompting"
    },
    {
        "text": "The transformer architecture uses self-attention mechanisms to process sequence data. It is the foundation of modern LLMs like GPT and BERT.",
        "source": "DL Concepts",
        "category": "architecture"
    }
]


async def seed_knowledge():
    """Seed the knowledge base with sample data"""
    for item in SAMPLE_KNOWLEDGE:
        await knowledge_base.add_knowledge(
            text=item["text"],
            source=item["source"],
            category=item["category"]
        )
    return len(SAMPLE_KNOWLEDGE)


async def clear_and_seed():
    """Clear knowledge base and reseed"""
    await knowledge_base.clear_knowledge()
    return await seed_knowledge()


if __name__ == "__main__":
    import asyncio
    count = asyncio.run(seed_knowledge())
    print(f"Seeded {count} knowledge items")