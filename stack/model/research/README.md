# LLM Stack Research

Decision-quality research for Layer 1 model selection. Each doc covers one question and ends with a recommendation or conclusion that feeds into the ADRs.

| Doc | Question | Status |
|---|---|---|
| [01 — Tool Use Requirements](01-tool-use-requirements.md) | What makes a model capable of reliable tool use? | complete |
| [02 — Model Candidates](02-model-candidates.md) | Which models are viable for Prosper0? | complete |
| [03 — Inference Runtime](03-inference-runtime.md) | Ollama vs. llama.cpp vs. alternatives? | complete |
| [04 — Orchestrator Loop](04-orchestrator-loop.md) | How does the agent loop work with a local model? | complete |
| [05 — Model-Agnostic Interface](05-model-agnostic-interface.md) | What is the interface contract between orchestrator and model? | complete |

## Conclusions

- **Runtime:** Ollama — HTTP API, Docker-native, easiest wiring, built on llama.cpp under the hood
- **Model:** Qwen2.5 7B (Q4_K_M, ~4.7GB) — strong tool use, Apache 2.0, fits any storage configuration
- **Fallback candidate:** Llama 3.2 3B for severely constrained environments; Qwen2.5 14B for more capable hardware
- **Interface:** Abstract `ModelBackend` class; `OllamaBackend` is the first implementation

See ADR-006 (model selection) and ADR-007 (inference runtime) for recorded decisions.
