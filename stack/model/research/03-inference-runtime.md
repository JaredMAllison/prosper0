# Inference Runtime

## The Question

Which runtime manages model loading, inference, and the API surface that the orchestrator talks to?

## Candidates

### Ollama — Recommended

Ollama wraps llama.cpp (and other backends) in a developer-friendly HTTP API with built-in model management. Pull a model with one command; run it immediately; switch models with a single config change.

**Key properties:**
- REST API at `http://localhost:11434` — `/api/chat` for conversation, `/api/generate` for completion
- OpenAI-compatible endpoint (`/v1/chat/completions`) — the orchestrator can use the same schema as any OpenAI client
- Native tool calling support — `tools` field in the request; `tool_calls` in the response
- Docker image: `ollama/ollama` — runs inside the container alongside the orchestrator
- Model storage: weights stored in a configurable directory, mappable to the USB drive volume
- One command to swap models: change the model tag in config, restart

**Docker Compose integration:**
```yaml
services:
  ollama:
    image: ollama/ollama
    volumes:
      - /mnt/prosper0/models:/root/.ollama  # weights live on the drive
    ports:
      - "11434:11434"

  ariel:
    build: ./stack/orchestrator
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - MODEL=qwen2.5:7b
    depends_on:
      - ollama
```

**Tradeoffs:**
- Slightly slower than raw llama.cpp (26 vs 28 tokens/sec on high-end GPU) — irrelevant for single-user work assistant
- Shorter effective context window than raw llama.cpp in some configurations — not a concern at 7B scale
- Adds a layer of abstraction — if Ollama has a bug, it's between you and the model

---

### llama.cpp — Alternative

The engine Ollama runs on top of. Direct binary, maximum control, maximum setup cost.

**When to choose:** You need raw performance, the overhead of Ollama's HTTP layer matters, or you're running on edge hardware where every MB counts.

**When not to choose:** You want fast iteration, Docker-native deployment, or easy model switching. That's Prosper0's use case.

---

### LM Studio / Jan — Not suitable

Desktop GUI applications. Not scriptable, not Docker-native, not appropriate for a containerized deployment.

---

### Docker Model Runner — Worth watching

Docker's native model runner (2026). Runs models directly inside Docker without a separate Ollama container. Early stage, API surface is still stabilizing. Not yet the default choice, but worth revisiting at Prosper1.

---

## Recommendation

**Ollama** in a Docker container, with model weights mounted from the drive path. Single HTTP API the orchestrator talks to. Model selection is one config line. Swap models without touching the orchestrator code.

This also means the version testing harness is trivial: point the orchestrator at a different Ollama model tag, run the prompt battery, compare outputs.

## Runtime ADR

See `prosper0-adr-007-inference-runtime.md`.
