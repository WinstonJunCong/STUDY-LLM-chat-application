from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes

app = FastAPI(title="LLM Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://llm-chat-frontend:8501",
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:80",
        "http://127.0.0.1:80",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Seed knowledge base on startup"""
    try:
        from app.services import vector_store
        from app.services.knowledge_seeder import seed_knowledge
        
        # Check if knowledge collection is empty, seed if needed
        try:
            client = vector_store.get_client()
            client.get_collection("knowledge")
        except Exception:
            # Collection doesn't exist, seed it
            print("Seeding knowledge base...")
            count = await seed_knowledge()
            print(f"Seeded {count} knowledge items")
    except Exception as e:
        print(f"Warning: Could not seed knowledge base: {e}")


@app.options("/{path:path}")
async def preflight_handler(path: str):
    return {"status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}