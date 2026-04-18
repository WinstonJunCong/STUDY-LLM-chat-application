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

---

## Challenges Faced

### 1. Token Streaming Not Working
**Problem:** Tokens arriving all at once instead of token-by-token.

**Root Cause:** Python `httpx` buffers SSE responses at multiple layers.

**Solution:** Used `aiter_text()` with manual buffer handling instead of `aiter_lines()`:

```python
buffer = ""
async for chunk in response.aiter_text():
    buffer += chunk
    while '\n\n' in buffer:
        line, buffer = buffer.split('\n\n', 1)
        yield line
```

### 2. Frontend Progression
**Problem:** Started with Streamlit, then Gradio - both had issues with true streaming.

**Solution:** Moved to React + Vite with ReadableStream for proper token-by-token display.

### 3. Docker Volume Mount on Windows
**Problem:** `/run/desktop/mnt/host/x/...` path conflicts with Docker Desktop on Windows.

**Solution:** Used named volumes instead of bind mounts in docker-compose.yml.

### 4. Testing Async HTTP Calls
**Problem:** Mocking `httpx.AsyncClient` with async context managers is complex.

**Attempted:** unittest.mock, aioresponses - both had issues with async context managers.

**Solution:** Used `respx` - a library specifically designed for mocking httpx requests. Clean and works perfectly.

### 5. Data Integrity - Orphaned Messages
**Problem:** User messages saved to DB before LLM call - if LLM fails, question remains orphaned.

**Solution:** Build history in-memory, save to DB only after successful LLM response.

---

## Potential Questions from Lead Developer

### Q1: Why not use WebSockets instead of SSE?
**A:** SSE is simpler for one-way streaming (server → client). WebSockets add complexity (connection management, reconnection logic). For this use case where user sends HTTP request and receives stream, SSE is the right choice.

### Q2: Why SQLite instead of PostgreSQL/MySQL?
**A:** This is a single-user, single-session application. SQLite is:
- Zero configuration
- No separate server needed
- Perfect for this scale
- Easy to migrate later if needed

### Q3: How does the frontend show tokens immediately?
**A:** Using `ReadableStream` with `TextDecoder`:
```javascript
const reader = response.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value, { stream: true });
  // Process SSE chunks...
}
```

### Q4: What happens if the user refreshes the page?
**A:** The frontend calls `/api/messages` on load to restore conversation history from SQLite. User sees their previous messages.

### Q5: How do you handle rate limiting?
**A:** The Gemini API returns 429 when rate limited. We catch this and display "Rate limit exceeded" to the user with a retry button that uses exponential backoff (1s → 2s → 4s → max 30s).

### Q6: Why save messages in-memory before calling LLM?
**A:** To maintain conversation context while avoiding orphaned messages in DB on failure. See "Data Integrity" challenge above.

### Q7: How do you test error handling without a real API key?
**A:** We use `respx` to mock HTTP responses:
```python
@respx.mock
async def test_503_returns_service_unavailable():
    respx.post(llm.GEMINI_API_URL).mock(
        return_value=httpx.Response(503)
    )
    # Test error handling...
```

### Q8: What's the security model?
**A:** No authentication - as specified in requirements. The API key is set via environment variable. In production, would recommend adding API key validation or rate limiting at the gateway level.

### Q9: Can this scale to multiple users?
**A:** Currently no - single SQLite database, single chat session. For multi-user:
- Add user_id to messages table
- Use PostgreSQL for concurrent connections
- Add authentication
- Implement rate limiting per user

### Q10: Why React instead of Next.js?
**A:** Simpler for this use case. Next.js adds SSR complexity not needed for a simple chat app. Can migrate to Next.js if SEO or SSR becomes important.

### Q11: What happens if the API returns an incomplete SSE stream?
**A:** If the stream ends unexpectedly, the frontend's `done` flag catches it. We also have a timeout mechanism - if no tokens arrive for 60 seconds, we treat it as a failure. The error handling in the generator ensures partial responses aren't saved to DB.

### Q12: How do you prevent XSS attacks from user input?
**A:** 
- User input is sent to the backend and passed directly to LLM
- LLM response (which could contain malicious content) is rendered with `react-markdown` which sanitizes HTML by default
- For extra safety, we could add input sanitization on the backend before storing in DB

### Q13: What if the database file gets corrupted?
**A:** SQLite has built-in crash recovery. For production:
- Add regular backups
- Use WAL mode for better concurrency: `PRAGMA journal_mode=WAL;`
- Add integrity checks on startup

### Q14: How would you handle very long conversations?
**A:** Current implementation passes ALL history to LLM. Issues:
- Context window limits (Gemini has ~1M tokens)
- Cost increases with history size

**Solutions:**
- Truncate old messages when limit reached
- Use summarization for older messages
- Paginate history in UI

### Q15: Why use Server-Sent Events instead of polling?
**A:** 
- SSE is push-based (real-time), polling is pull-based
- Lower latency - tokens arrive immediately
- More efficient - no repeated HTTP requests
- Simpler than WebSockets for one-way data flow

### Q16: How do you handle connection drops during streaming?
**A:** 
- Frontend tracks connection state
- On disconnect during streaming, user can retry
- Partial responses (if any) are still saved since DB save happens after each successful token batch
- Could add auto-retry with backoff for intermittent network issues

### Q17: What's the cost implication of this architecture?
**A:** 
- Gemini 3.1 Flash Lite: Free tier available (~15 RPM, ~1M TPM)
- SQLite: Free
- Docker: Free (local) or ~$5-10/month for cloud hosting
- Frontend hosting: Free (Vercel/Netlify)

### Q18: How do you ensure the LLM doesn't respond with harmful content?
**A:** Currently not implemented. For production:
- Use Gemini's built-in safety settings
- Add content filtering on responses before displaying
- Implement prompt injection detection

### Q19: What's the retry strategy for failed requests?
**A:** 
- Client-side: Exponential backoff (1s → 2s → 4s → 8s → max 30s)
- Server-side: Not implemented - relying on Gemini's retry headers
- After max retries, show permanent error with manual retry button

### Q20: How would you add authentication?
**A:** Options:
- API keys in headers (simple)
- JWT tokens (standard)
- OAuth2 with Google/GitHub login

For this project, would add:
1. `users` table with password hash
2. `/api/auth/login` and `/api/auth/register` endpoints
3. Add `user_id` to messages table
4. Protected routes with dependency injection

### Q21: What's the difference between async and sync streaming?
**A:** 
- **Sync:** Block until data arrives (simpler, blocks thread)
- **Async:** Non-blocking, allows handling multiple concurrent requests

We use async streaming with `async for` - this is essential for FastAPI to handle multiple users simultaneously without thread blocking.

### Q22: How do you handle the Gemini API response format changes?
**A:** 
- Current parsing looks for `candidates[0].content.parts[0].text`
- API could change structure in future
- Solution: Add response validation, log unexpected formats, update parsing code when Gemini updates

### Q23: Why not use a queue system like Celery?
**A:** 
- Celery adds complexity (message broker like Redis/RabbitMQ)
- This is synchronous: user waits for response
- Queue makes sense for background jobs, not real-time chat
- If we wanted async (user gets notified when done), we'd use a task queue

### Q24: How would you handle multiple concurrent users?
**A:** Current limitations:
- SQLite not great with concurrent writes
- Single FastAPI worker by default

Solutions:
- Use PostgreSQL instead of SQLite
- Add connection pooling
- Use multiple FastAPI workers with uvicorn: `uvicorn --workers 4`
- Add rate limiting per user

### Q25: What's your deployment strategy?
**A:** 
- Local: `docker-compose up`
- Cloud: Could use AWS ECS, Google Cloud Run, or simple VPS
- Frontend: Vercel/Netlify (free)
- Database: Could keep SQLite on ephemeral disk, or migrate to PostgreSQL (Supabase, Neon)

### Q26: How do you handle API key rotation?
**A:** Currently: requires app restart to pick up new key. For production:
- Store encrypted API keys in secrets manager
- Add endpoint to rotate key without restart
- Implement key versioning for rollback

### Q27: What's the test coverage strategy?
**A:** 
- Unit tests: Core business logic (DB, LLM, routes)
- Integration tests: End-to-end with test API key
- Not tested: Frontend interactions (would use Playwright/Cypress)
- Coverage goal: 80% on backend

### Q28: Why not use an ORM like SQLAlchemy?
**A:** 
- SQLAlchemy adds abstraction overhead
- SQLite with raw SQL is simple and sufficient for this use case
- Fewer dependencies = smaller attack surface
- Can migrate to SQLAlchemy if complexity grows

### Q29: How do you handle message formatting edge cases?
**A:** 
- Empty messages: Rejected with 422 validation error
- Very long messages: Limited by Gemini's input size
- Special characters: Handled by JSON encoding in SSE
- Markdown: `react-markdown` handles most cases, code blocks styled separately

### Q30: What's the upgrade path for the LLM model?
**A:** 
- Change `GEMINI_MODEL` in code or env variable
- Update tests to reflect new model name
- No code changes needed in API - model is just part of the URL
- Could add model selection UI in future