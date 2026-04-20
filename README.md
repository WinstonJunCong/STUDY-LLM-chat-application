# Winston - LLM Chat Application (llama.cpp Version)

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
- Docker Desktop with GPU enabled

### Check GPU Access
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

If this shows your GPU info, you're ready.

## Setup

### 1. Configure GPU Access in Docker Desktop
- Open Docker Desktop → Settings → Resources → GPU
- Enable GPU access

### 2. Start the Application

```bash
docker-compose up --build
```

This will:
1. **Download the model** on first run (~1GB, may take a few minutes)
2. Start **llama.cpp server** on port 8080
3. Start **Backend** on port 8000
4. Start **Frontend** on port 8501

**First run:** Model download + loading may take 5-10 minutes.

### 3. Open the App
Navigate to http://localhost:8501

## Model

This branch uses **Mistral-7B-v0.1 Q4_K_M** (~4GB):
- Good quality for chat
- GGUF format from TheBloke

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
- Check logs: `docker logs winston-model-downloader`

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
| **vllm** | Qwen (local) | ✅ 6GB+ | ~10GB | ❌ No |
| **llamacpp** | Qwen (local) | ✅ 4GB+ | ~2GB | ❌ No |

## License

MIT