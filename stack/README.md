# Layer 1: LLM Stack

The local inference engine for Ariel von Prosper0.

**Model:** Qwen2.5 7B (Apache 2.0, quantized Q4/Q5)  
**Runtime:** Ollama in Docker  
**Interface:** Model-agnostic — swap the model without touching the orchestrator

## Structure

```
stack/
├── orchestrator/
│   ├── backend.py        ← ModelBackend ABC + ModelResponse/ToolCall dataclasses
│   ├── ollama.py         ← OllamaBackend adapter (Ollama /api/chat + /api/tags)
│   ├── loop.py           ← Agent loop: generate → gate → tool result → repeat
│   ├── prompt.py         ← build_system_prompt() — persona + memory + skill injection
│   ├── config.py         ← tools.config.yaml loader
│   └── main.py           ← Entry point (reads env, starts REPL)
├── mcp/
│   ├── tools/
│   │   └── read_file.py  ← Read a vault file; path traversal protection
│   ├── registry.py       ← make_tool_executor(vault_root) → executor callable
│   └── definitions.py    ← Tool JSON schemas passed to Ollama
├── model/
│   └── research/         ← Model selection research docs (Q1–Q5)
└── tools.config.yaml     ← Operator-controlled tool permissions (AI-immutable)
```

## The Agent Loop

```
build_system_prompt(mode, session_id)
        ↓
backend.generate(messages, tools, system_prompt)
        ↓
  tool_call present?
  ├── YES → GateCaller.call(tool_name, path, executor)
  │           ↓ enforcement chain gates → executor runs → result appended
  │           ↓ loop back to generate
  └── NO  → return text to operator
```

Max-iteration guard (default 20) prevents infinite loops. Enforcement rejections surface as tool results — the model sees the error and responds rather than the loop crashing.

## tools.config.yaml

Operator-written. AI-immutable (read-only Docker mount). Loaded at startup by the enforcement chain. Governs which tools and vault paths are accessible. `signed_by` field supports Ed25519 employer signature verification (see ADR-003).

## Model Swapping

Change one line in the environment:

```bash
OLLAMA_MODEL=qwen2.5:14b docker compose up
```

The orchestrator never imports `httpx` or knows about Ollama directly — it talks to `ModelBackend`. A `LlamaCppBackend` would look identical from the orchestrator's perspective.

## ADRs

- [ADR-006](../spec/prosper0-adr-006-model-selection.md) — Qwen2.5 7B selected
- [ADR-007](../spec/prosper0-adr-007-inference-runtime.md) — Ollama in Docker
- [ADR-008](../spec/prosper0-adr-008-orchestrator-design.md) — Orchestrator loop design
