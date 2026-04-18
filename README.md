# Winston - LLM Chat Application

A simple LLM chat interface with token-by-token streaming, built with FastAPI and React.

## Features

- **Token-by-token streaming** via Server-Sent Events (SSE)
- **Chat session persistence** with SQLite - LLM remembers conversation history
- **Error handling** for API failures (503, 429, 403, 400) with friendly messages
- **Markdown rendering** for LLM responses (bold, headers, code blocks, lists)
- **Exponential backoff retry** on errors (1s → 2s → 4s → max 30s)
- **React frontend** with typing indicators and ghost bubble

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python) |
| LLM | Google Gemini 3.1 Flash Lite |
| Database | SQLite |
| Frontend | React + Vite |
| HTTP Client | httpx (async streaming) |
| Testing | pytest + respx |

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Gemini API key (get from https://aistudio.google.com/app/apikey)

### Running with Docker

1. Copy `.env` and add your API key:

   ```
   GEMINI_API_KEY=your_key_here
   ```

2. Start the app:

   ```bash
   docker-compose up --build
   ```

3. Open http://localhost:8501

### Running without Docker

**Backend:**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend-react
npm install
npm run dev
```

Open http://localhost:5173

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message, returns SSE stream |
| `/api/messages` | GET | Get chat history |
| `/api/messages` | DELETE | Clear chat history |
| `/api/reset` | POST | Reset conversation |

## Testing

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run tests
python -m pytest backend/tests/ -v
```

**Test Coverage:** 19 tests covering:
- Database operations (add, get, clear, roles)
- API routes (validation, messages, reset)
- LLM error handling (503, 429, 403, 400, no API key, streaming)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI   │────▶│  Gemini API │
│  Frontend   │◀────│   Backend   │◀────│             │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   SQLite    │
                    │  (History)  │
                    └─────────────┘
```

### Key Implementation Details

#### SSE Streaming

The streaming endpoint uses Server-Sent Events (SSE) to stream tokens as they arrive:

```python
async def token_generator():
    async for token in llm.stream_llm_response(history_formatted):
        yield token  # Immediate delivery to frontend
```

#### Error Handling

All API errors are caught and converted to user-friendly messages:

| Error Code | Message |
|------------|---------|
| 503 | "Service temporarily unavailable. Please try again later." |
| 429 | "Rate limit exceeded. Please wait before sending another message." |
| 403 | "Invalid API key. Please check your GEMINI_API_KEY." |
| 400 | "Bad request: {details}" |

## Project Structure

```
winston/
├── backend/
│   ├── app/
│   │   ├── api/routes.py        # SSE streaming endpoint
│   │   ├── services/
│   │   │   ├── llm.py           # Gemini API integration
│   │   │   └── database.py      # SQLite operations
│   │   └── main.py              # FastAPI app
│   ├── tests/                   # 19 passing tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend-react/
│   ├── src/App.jsx              # React chat UI
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml           # Multi-container deployment
├── .env                         # Template (GEMINI_API_KEY)
└── pytest.ini
```

## License

MIT