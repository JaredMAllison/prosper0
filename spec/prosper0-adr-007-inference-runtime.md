---
title: "Prosper0-ADR-007: Inference Runtime — Ollama"
type: adr
project: Prosper0
status: accepted
date: 2026-04-20
tags: [adr, prosper0, inference-runtime, ollama]
---

## Context

The orchestrator needs a runtime that loads model weights, runs inference, and exposes an API. The runtime must be Docker-native (the entire Prosper0 stack runs in containers), support OpenAI-compatible tool calling, and allow model weights to be stored on an external drive volume.

## Decision

**Ollama** — running as a Docker container (`ollama/ollama`) alongside the orchestrator container.

- REST API at `http://ollama:11434` (internal Docker network)
- OpenAI-compatible endpoint (`/v1/chat/completions`) — uses standard tool calling schema
- Model weights stored in a configurable volume mapped to the drive path (`/mnt/prosper0/models`)
- Model selection is one config line: change `MODEL=qwen2.5:7b` to any Ollama-supported tag
- Built on llama.cpp under the hood — no raw inference performance lost for single-user workloads

**Rejected alternatives:**
- **llama.cpp directly:** Maximum performance, minimum setup convenience. The ~2 token/sec advantage over Ollama is irrelevant for a single-user work assistant. Setup and model management complexity is not worth it.
- **LM Studio / Jan:** Desktop GUI applications. Not scriptable, not Docker-native.
- **Docker Model Runner:** Promising but API surface still stabilizing as of 2026-04. Revisit at Prosper1.

## Consequences

**Enables:**
- One-command model switch: update `MODEL` env var, restart container
- Version testing harness uses `GET /api/tags` to enumerate available models — no code changes to test a new model
- The orchestrator's `OllamaBackend` adapter can be replaced with any `ModelBackend` implementation without changing the orchestrator loop
- Drive-relative model storage: `volumes: [/mnt/prosper0/models:/root/.ollama]` — weights travel with the drive

**Forecloses:**
- Direct llama.cpp optimizations (custom context sizes, batch parameters) without moving off Ollama

**Monitoring:** If Ollama introduces a breaking API change, the `OllamaBackend` adapter is the only file that needs updating. The interface contract (`ModelBackend`) and the orchestrator loop are insulated.
