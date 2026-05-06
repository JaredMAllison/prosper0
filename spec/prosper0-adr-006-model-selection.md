---
title: "Prosper0-ADR-006: Model Selection — Qwen2.5 7B as Primary"
type: adr
project: Prosper0
status: accepted
date: 2026-04-20
tags: [adr, prosper0, model-selection, llm]
---

## Context

Ariel (the AI assistant running on Prosper0) requires a local model capable of reliable tool use, instruction following, and task-management reasoning. Model selection is job-role dependent — a grunt IT role needs less than a Knowledge Manager role. This ADR records the decision for the initial deployment configuration. It is expected to be revisited at each new job instance (Prosper1, Prosper2, etc.).

**Hardware context:** Development and testing on Gretchen (CPU-only, integrated chipset GPU). Production runs on employer-provided hardware via USB drive — expected to be more capable, potentially with discrete GPU.

**Storage context:** Flexible configurations (USB-first, host-first, hybrid). Size is tracked, not fixed. Model must fit comfortably within any expected configuration.

## Decision

**Primary model:** Qwen2.5 7B (Q4_K_M quantization)
- Size: ~4.7 GB
- License: Apache 2.0 (fully open source, no employer license concerns)
- Context length: 128K tokens
- Tool use: Native (OpenAI-compatible function calling via Ollama)
- Ollama tag: `qwen2.5:7b`

**Fallback (minimal deployment):** Llama 3.2 3B (Q4_K_M)
- Size: ~2.0 GB
- License: Llama 3 Community License
- For CPU-only hardware where 7B inference speed is unacceptable, or extremely storage-constrained configurations

**High-capability option (knowledge-intensive roles):** Qwen2.5 14B or Llama 3.3 70B
- For Knowledge Manager, analyst, or architect roles requiring deeper reasoning
- 70B only viable on employer hardware with 24GB+ VRAM

**Rejected candidates:**
- Mistral 7B: shorter context (32K vs 128K), slightly weaker tool use reliability
- Phi-4 14B: 16K context too short for vault-heavy prompts; MIT license is clean but context gap is disqualifying
- Gemma 2: custom license adds friction; no clear capability advantage over Qwen2.5

## Consequences

**Enables:**
- Apache 2.0 license — no conversation with employer IT about model licensing
- 128K context accommodates system prompt + memory injection + conversation history without trimming in typical work sessions
- Native tool calling produces reliable structured output; orchestrator parsing is deterministic
- Same model tag works on CPU (Gretchen for dev) and GPU (employer hardware for prod)

**Forecloses:**
- Using a single model choice permanently — this ADR is expected to be superseded at each job instance
- Running 70B-class models on USB-first deployments (too large)

**Monitoring:** If inference speed on employer CPU hardware is below ~3 tokens/sec, step down to 3B. If role requires complex document synthesis, step up to 14B. Model selection is a deployment-time decision, not a code change.
