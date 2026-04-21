# QuikSesh - LLM Chat Application (llama.cpp Version)

A real-time LLM chat application with token-by-token streaming, using a local llama.cpp server instead of cloud APIs.

## ⚠️ GPU Required

**This branch requires a GPU to run.** Without a CUDA-capable GPU, this will not work.

See [Requirements](#requirements) section below.

## Features

- **Token-by-token streaming** via Server-Sent Events (SSE)
- **Local LLM** - No cloud API calls, runs entirely on your machine
- **Chat session persistence** with SQLite - LLM remembers conversation history
- **Error handling** for llama.cpp-specific errors (OOM, model not found, GPU errors)
- **Markdown rendering** for LLM responses (bold, headers, code blocks, lists)
- **Exponential backoff retry** on errors (1s → 2s → 4s → max 30s)
- **React frontend** with typing indicators and ghost bubble
- **Lightweight** - Much smaller than VLLM (~2GB vs ~10GB)

## Requirements

### Hardware
- **NVIDIA GPU with 4GB+ VRAM** (e.g., RTX 2060, RTX 3060, RTX 4060)
- Without GPU, llama.cpp will run on CPU (very slow)

### Software
- NVIDIA Driver (installed on Windows)
- NVIDIA Container Toolkit (for Docker GPU access)

### Check GPU Access
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

If this shows your GPU info, you're ready.

## Setup

### 1. Start the Application

```bash
docker-compose up --build
```

This will:
1. **Download the model** on first run (~1GB, may take a few minutes)
2. Start **llama.cpp server** on port 8080
3. Start **Backend** on port 8000
4. Start **Frontend** on port 8501

**First run:** Model download + loading may take 5-10 minutes.

### 2. Open the App
Navigate to http://localhost:8501

## Model

This branch uses **Qwen3.5-4B-Q4_K_M** (~4GB):
- Good quality for chat
- GGUF format from UnSloth

To change the model, edit `docker-compose.yml`:
```yaml
command: [
  "-m", "/models/your-model.gguf",
  ...
]
```

## Troubleshooting

### Model Download Stuck
- First run downloads ~1GB from HuggingFace
- Check logs: `docker logs QuikSesh-model-downloader`

### CUDA Out of Memory
- Try a smaller model
- Reduce GPU layers: change `-ngl 32` to `-ngl 16`

### llama.cpp Won't Start
- Ensure Docker has GPU access enabled
- Check Docker Desktop → Settings → Resources → GPU

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message, returns SSE stream |
| `/api/messages` | GET | Get chat history |
| `/api/messages` | DELETE | Clear chat history |
| `/api/reset` | POST | Reset conversation |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI   │────▶│ llama.cpp   │
│  Frontend   │◀────│   Backend   │◀────│ (Local GPU) │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   SQLite    │
                    │  (History)  │
                    └─────────────┘
```

## Testing

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run tests
python -m pytest backend/tests/ -v
```

**Test Coverage:** 18 tests covering:
- Database operations (add, get, clear, roles)
- API routes (validation, messages, reset)
- LLM error handling (OOM, model not found, GPU errors, streaming)

## Error Handling

| Error | Cause | Message |
|-------|-------|---------|
| OOM | GPU out of memory | "GPU out of memory. Try a smaller model." |
| Model not found | Missing GGUF file | "Model not found. Please check model file." |
| GPU error | CUDA issue | "GPU error: {details}" |
| Other | Unknown | Exposed for debugging |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `LLAMACPP_URL` | http://llamacpp:8080 | llama.cpp API URL |

## Comparison: All Branches

| Branch | Model | GPU | Size | Internet |
|--------|-------|-----|------|----------|
| **main** | Gemini (cloud) | ❌ | N/A | ✅ Yes |
| **llamacpp** | Qwen (local) | ✅ 4GB+ | ~2GB | ❌ No |

---

## Challenges Faced

### 1. Wrong Docker Image - No GPU Support
**Problem:** Using `ghcr.io/ggml-org/llama.cpp:server` has NO CUDA support compiled in.

**Evidence in logs:**
```
load_backend: loaded CPU backend from /app/libggml-cpu-haswell.so
warning: no usable GPU found, --gpu-layers option will be ignored
```

**Solution:** Use the CUDA variant: `ghcr.io/ggml-org/llama.cpp:server-cuda`

---

### 2. GPU Memory Constraints
**Problem:** RTX 2060 has only 6GB VRAM, but Qwen3.5-4B needs more.

**Evidence in logs:**
```
llama_params_fit_impl: projected to use 11762 MiB of device memory vs. 4911 MiB free
llama_params_fit_impl: context size reduced from 262144 to 20480
```

**Solutions:**
- Use a smaller model (Qwen2.5-1.5B instead of 4B)
- Use lighter quantization: Q4 instead of Q8

---

### 3. Model Download on First Run
**Problem:** Docker Alpine image doesn't have wget/curl by default.

**Solution:** Install curl first:
```yaml
command: |
  sh -c "mkdir -p /models && \
  apk add --no-cache curl && \
  curl -L -o /models/model.gguf 'https://...'"
```

---

### 4. Healthcheck Race Condition
**Problem:** Backend starts before llama.cpp is ready, causing connection failures.

**Solution:** Add healthcheck with `service_healthy` dependency:
```yaml
depends_on:
  llamacpp:
    condition: service_healthy
```

---

### 5. Slow Prompt Processing (CPU Mode)
**Problem:** Prompt evaluation taking 3,631ms per token instead of near-instant.

**Evidence:**
```
prompt eval time = 90788.57 ms / 25 tokens (3631.54 ms per token)
```

**Root Cause:** Still running on CPU despite CUDA image. Check:
- Ensure `--gpus all` flag is passed in docker-compose
- Verify nvidia-container-toolkit is installed

---

### 6. Think Tags Display
**Problem:** Qwen models output `<think>...</think>` tags in response.

**Solution:** Remove chat template and use this when launching llama-server:
```
"--reasoning-format", "deepseek",
```

---

## Troubleshooting

### GPU Not Detected in Container
```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```
If this fails, install NVIDIA Container Toolkit.

### CUDA Out of Memory
```
llama_params_fit_impl: context size reduced from 262144 to 20480
```
**Fix:** Use smaller model or reduce `-ngl` value.

### Model Download Fails
- Check internet connection
- Verify HuggingFace URL is correct
- Check disk space: `df -h`

### Container Won't Start
```bash
# Check logs
docker logs QuikSesh-llamacpp

# Check GPU access
docker exec QuikSesh-llamacpp nvidia-smi
```

### Slow Responses
- First request always slow (model loading)
- Use smaller model
- Ensure GPU is being used (check logs for "CUDA0")

---

## Test Case Build to Assure Quality

### Test Suite Overview

| Test File | Tests | Coverage |
|----------|-------|----------|
| `test_database.py` | 5 | Add, get, clear, message roles |
| `test_routes.py` | 6 | Validation, messages, reset |
| `test_llm.py` | 7 | Error handling, streaming, API |

**Total:** 18 passing tests

### Running Tests

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run all tests
python -m pytest backend/tests/ -v

# Run specific test file
python -m pytest backend/tests/test_llm.py -v
```

### Test Coverage Goals

| Area | Current Coverage |
|------|-----------------|
| Database | 100% |
| API Routes | 100% |
| LLM Error Handling | 100% |

### Key Test Cases

#### Database Tests
- `test_add_message` - Verify message save
- `test_get_all_messages_returns_dict` - Verify message retrieval
- `test_clear_messages` - Verify cleanup
- `test_message_roles` - Verify role (user/assistant)

#### API Route Tests
- `test_chat_empty_message_returns_422` - Validation
- `test_get_messages_with_data` - History retrieval
- `test_reset_clears_conversation` - Reset functionality

#### LLM Error Tests
- `test_oom_returns_friendly_message` - GPU OOM handling
- `test_model_not_found_returns_friendly_message` - Missing model
- `test_gpu_error_returns_friendly_message` - CUDA errors
- `test_successful_response_streams_tokens` - Streaming verification

---

## VLLM vs llama.cpp Comparison

| Feature | VLLM | llama.cpp |
|---------|-----|-----------|
| **Image Size** | ~10GB | ~2GB |
| **GPU VRAM Required** | 6GB++ | 4GB+ |
| **Startup Time** | ~2 minutes | ~10 seconds |
| **First Request** | not tested | ~90 seconds |
| **FFA Performance** | not tested | Good |
| **Easy Quantization** | No | Yes (GGUF) |
| **Docker Images** | Official | Official |
| **API Compatibility** | OpenAI | OpenAI |
| **Local Deployment** | Yes | Yes |
| **Mobile/GPU Support** | CUDA only | CUDA, ROCm, CPU |

### When to Use VLLM
- Have GPU with 8GB+ VRAM
- Need higher throughput
- Running multiple models

### When to Use llama.cpp
- Limited GPU memory (4-6GB)
- Need smaller image
- Want quantization flexibility

---

## Potential Questions from Lead Developer

### Q1: Why not use WebSockets instead of SSE?
**A:** SSE is simpler for one-way streaming. WebSockets add connection management complexity. For this use case (HTTP request → stream response), SSE is the right choice.

### Q2: Why SQLite instead of PostgreSQL?
**A:** Single-user, single-session app. SQLite is zero-config, no separate server needed, perfect for this scale.

### Q3: How does the frontend stream tokens?
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
**A:** Frontend calls `/api/messages` on load to restore conversation history from SQLite.

### Q5: How do you handle rate limiting?
**A:** llama.cpp doesn't have rate limits like cloud APIs. GPU memory is the limiting factor.

### Q6: What's the security model?
**A:** No authentication. API runs locally. In production, would recommend gateway-level security.

### Q7: Can this scale to multiple users?
**A:** Currently no - single SQLite, single session. For multi-user:
- Add user_id to messages
- Use PostgreSQL
- Add authentication

### Q8: Why React instead of Next.js?
**A:** Simpler for this use case. Next.js adds SSR complexity not needed.

### Q9: What if the database gets corrupted?
**A:** SQLite has crash recovery. For production:
- Add regular backups
- Use WAL mode: `PRAGMA journal_mode=WAL;`

### Q10: How would you handle very long conversations?
**A:** Issues with current approach:
- Context window limits
- Memory increases with history

**Solutions:**
- Truncate old messages
- Use summarization
- Paginate history

### Q11: Why use SSE instead of polling?
**A:** SSE is push-based (real-time), lower latency, more efficient than repeated HTTP polling.

### Q12: How do you handle connection drops during streaming?
**A:** Frontend tracks connection state. On disconnect, user can retry. Partial responses are saved.

### Q13: What's the cost of running locally?
**A:**
- Electricity: ~$10-20/month
- Hardware: One-time purchase (GPU)
- No API costs

### Q14: How do you choose the right model?
**A:** Consider:
- VRAM available (4GB = 1.5B model, 6GB = 4B model, 8GB+ = 7B)
- Quality vs speed tradeoff
- Quantization level (Q2-Q8)

### Q15: What's the upgrade path for the model?
**A:** Just change the GGUF file and Docker image tag. No code changes needed.

### Q16: How do you ensure GPU is being used?
**A:** Check logs for:
- `CUDA0 model buffer size`
- `offloading X layers to GPU`
- Fast prompt processing (<10ms)

### Q17: Why different Docker images (server vs server-cuda)?
**A:** Default image has NO GPU support. Must use `-cuda` variant for GPU acceleration.

### Q18: How do you handle the cold start problem?
**A:** Use `restart: unless-stopped` to keep container running. First request will still be slow, but subsequent ones are fast.

### Q19: What's the difference between -ngl values?
**A:** Number of layers offloaded to GPU:
- `-ngl 32` = all layers (needs more VRAM)
- `-ngl 0` = CPU only (slow)
- `-ngl 16` = half (less VRAM)

### Q20: How do you determine the right context size?
**A:** Based on VRAM. Formula: ~100MB per 1K context. With 6GB, max ~60K context recommended.

### Q21: Why use GGUF format?
**A:** Optimized for local inference, supports quantization, memory-mapped loading.

### Q22: What's the difference between Q2, Q4, Q8 quantization?
**A:** Quality vs size:
- Q2: Smallest, lowest quality
- Q4: Balanced (recommended)
- Q8: Largest, highest quality

### Q23: How do you debug the LLM responses?
**A:** Check Docker logs:
```bash
docker logs QuikSesh-llamacpp
```

### Q24: What's the retry strategy for errors?
**A:** Client-side exponential backoff. Server-side retries based on error type:
- OOM: Suggest smaller model
- Model not found: Check file exists

### Q25: How do you add system prompts?
**A:** Added in `llm.py`:
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant. Be concise and direct."}
]
```

### Q26: What's the healthcheck endpoint?
**A:** llama.cpp provides `/v1/models` endpoint. Used in docker-compose:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/v1/models"]
```

### Q27: How do you handle think tags?
**A:** Filter in frontend before display:
```javascript
text.replace(/<think>[\s\S]*?<\/think>/g, "")
```

### Q28: What's the model loading time?
**A:** First request: ~90 seconds. Subsequent: <1 second (cached in VRAM).

### Q29: How do you choose between local and cloud?
**A:** Local: No internet, privacy, no API costs. Cloud: More powerful models, less setup.

### Q30: What's the deployment path?
**A:** Local is `docker-compose up`. Cloud deployment would require:
- Cloud GPU instance (Lambda Cloud, Paperspace, etc.)
- Docker container hosting
- Optional: migrate to cloud-managed LLM APIs

---

## License

MIT