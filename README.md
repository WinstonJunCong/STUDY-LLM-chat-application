# Winston - LLM Chat Application (VLLM Version)

A real-time LLM chat application with token-by-token streaming, using a local VLLM instance instead of cloud APIs.

## ⚠️ GPU Required

**This branch requires a GPU to run.** Without a CUDA-capable GPU, this will not work.

See [Requirements](#requirements) section below.

## Features

- **Token-by-token streaming** via Server-Sent Events (SSE)
- **Local LLM** - No cloud API calls, runs entirely on your machine
- **Chat session persistence** with SQLite - LLM remembers conversation history
- **Error handling** for VLLM-specific errors (500, 503, 404, CUDA OOM)
- **Markdown rendering** for LLM responses (bold, headers, code blocks, lists)
- **Exponential backoff retry** on errors (1s → 2s → 4s → max 30s)
- **React frontend** with typing indicators and ghost bubble

## Requirements

### Hardware
- **NVIDIA GPU with 6GB+ VRAM** (e.g., RTX 2060, RTX 3060, RTX 4060)
- Without GPU, this will not work

### Software
- NVIDIA Driver (installed on Windows)
- NVIDIA Container Toolkit (for Docker GPU access)
- Docker Desktop with GPU enabled

### Check GPU Access
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

If this shows your GPU info, you're ready. If not, install NVIDIA Container Toolkit.

## Setup

### 1. Configure GPU Access in Docker Desktop
- Open Docker Desktop → Settings → Resources → GPU
- Enable GPU access

### 2. Start the Application

```bash
docker-compose up --build
```

This will start:
- **VLLM** on port 8001 (loads the model)
- **Backend** on port 8000
- **Frontend** on port 8501

**First run:** VLLM will download the model (~2GB), which may take several minutes.

### 3. Open the App
Navigate to http://localhost:8501

## Troubleshooting

### VLLM Won't Start
- Ensure Docker has GPU access enabled
- Check Docker Desktop → Settings → Resources → GPU

### CUDA Out of Memory
- Try a smaller model (1B instead of 3B)
- Reduce `MAX_NUM_SEQS` in docker-compose.yml

### Model Download Stuck
- First run can take 5-10 minutes depending on internet speed
- Check VLLM logs: `docker logs winston-vllm`

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
│   React     │────▶│   FastAPI   │────▶│    VLLM     │
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

**Test Coverage:** 19 tests covering:
- Database operations (add, get, clear, roles)
- API routes (validation, messages, reset)
- LLM error handling (500, 503, 404, CUDA OOM, unknown errors, streaming)

## Error Handling

| Error Code | Cause | Message |
|------------|-------|---------|
| 500 | Model not loaded | "Server error. Model may not be loaded yet" |
| 503 | Service unavailable | "Service unavailable. Please try again later" |
| 404 | Model not found | "Model not found. Check VLLM_MODEL config" |
| 507 | CUDA OOM | "GPU out of memory. Try smaller model" |
| Other | Unknown | Exposed for debugging |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `VLLM_URL` | http://vllm:8000 | VLLM API URL |
| `VLLM_MODEL` | meta-llama/Llama-3.2-1B-Instruct | Model to use |

To change the model, edit `.env` or docker-compose.yml:
```bash
VLLM_MODEL=meta-llama/Llama-3.2-3B-Instruct
```

## Available Models

| Model | VRAM Needed | Speed | Quality |
|-------|-------------|-------|---------|
| Llama 3.2 1B | ~2GB | Fast | Good |
| Llama 3.2 3B | ~6GB | Medium | Better |
| Phi-3.5-mini | ~4GB | Fast | Good |
| Mistral 7B | ~14GB | Slow | Best |

## Comparison: This Branch vs Main Branch

| Feature | This (VLLM) | Main (Gemini) |
|---------|-------------|---------------|
| GPU Required | ✅ Yes | ❌ No |
| Internet Required | ❌ No | ✅ Yes |
| Cost | Free | API calls |
| Speed | Depends on GPU | Depends on API |
| Privacy | 100% local | Data sent to Google |

## License

MIT