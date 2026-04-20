# Model Candidates

All models run 100% locally. Weights downloaded once; no internet required at runtime; no cloud API.

## Evaluation Criteria

1. Native tool calling support (non-negotiable)
2. Instruction following quality
3. Size at Q4_K_M quantization (disk + RAM)
4. License (for employer transparency)
5. Inference speed on CPU/modest GPU

## Candidates

### Qwen2.5 7B — **Primary Recommendation**

| Field | Value |
|---|---|
| Developer | Alibaba |
| License | Apache 2.0 (fully open source) |
| Size (Q4_K_M) | ~4.7 GB |
| Context length | 128K tokens |
| Tool use | Native (OpenAI-compatible) |
| Ollama tag | `qwen2.5:7b` |

**Why:** Best combination of size, tool use reliability, and instruction following in the 7B class. Apache 2.0 means no license conversation with IT. 128K context is larger than needed for task management but gives headroom for vault content injection. Strong structured output performance — consistent JSON tool calls.

**Tradeoff:** 7B models are less capable than 14B+ for complex reasoning. For task management and vault read/write, 7B is sufficient.

---

### Llama 3.2 3B — Compact Fallback

| Field | Value |
|---|---|
| Developer | Meta |
| License | Llama 3 Community License |
| Size (Q4_K_M) | ~2.0 GB |
| Context length | 128K tokens |
| Tool use | Native (OpenAI-compatible) |
| Ollama tag | `llama3.2:3b` |

**Why:** Smallest viable model with native tool calling. For severely storage-constrained deployments or low-powered hardware. Noticeably less capable than 7B models on complex instructions.

**Tradeoff:** Capability drop is real at 3B. Use as a fallback, not a first choice.

---

### Llama 3.3 70B — High-Capability Option

| Field | Value |
|---|---|
| Developer | Meta |
| License | Llama 3 Community License |
| Size (Q4_K_M) | ~43 GB |
| Context length | 128K tokens |
| Tool use | Native (OpenAI-compatible) |
| Ollama tag | `llama3.3:70b` |

**Why:** Best tool use and reasoning in the open-weight class. For deployments where storage isn't constrained and the host has a capable GPU (24GB+ VRAM). Impractical for USB-first deployments.

**Tradeoff:** 43GB is most of a 64GB USB drive before the OS, Docker image, or vault. Only viable for host-first configurations.

---

### Mistral 7B — Alternative 7B

| Field | Value |
|---|---|
| Developer | Mistral AI |
| License | Apache 2.0 |
| Size (Q4_K_M) | ~4.1 GB |
| Context length | 32K tokens |
| Tool use | Native (OpenAI-compatible) |
| Ollama tag | `mistral:7b` |

**Why:** Fastest tokens/sec of the 7B candidates on CPU. Apache 2.0.

**Tradeoff:** 32K context is shorter than Qwen2.5's 128K. For vault-heavy prompts this could become a constraint. Slightly weaker tool use reliability than Qwen2.5 in benchmarks.

---

### Phi-4 14B — Microsoft Compact

| Field | Value |
|---|---|
| Developer | Microsoft |
| License | MIT |
| Size (Q4_K_M) | ~8.5 GB |
| Context length | 16K tokens |
| Tool use | Native (OpenAI-compatible) |
| Ollama tag | `phi4:14b` |

**Why:** MIT license (cleanest possible). Strong reasoning per parameter. Good for hosts with 10-12GB VRAM.

**Tradeoff:** 16K context is the shortest of the candidates. For Ariel, context includes system prompt + memory + conversation history + vault content — 16K could be tight.

---

## Size Summary

| Model | Size (Q4_K_M) | Suitable for USB-first? |
|---|---|---|
| Llama 3.2 3B | ~2.0 GB | Yes |
| Mistral 7B | ~4.1 GB | Yes |
| Qwen2.5 7B | ~4.7 GB | Yes |
| Phi-4 14B | ~8.5 GB | Yes (with headroom) |
| Llama 3.3 70B | ~43 GB | No (host-first only) |

## Recommendation

**Qwen2.5 7B (Q4_K_M)** for the primary configuration. Apache 2.0, native tool calling, 128K context, fits comfortably in any storage configuration. Llama 3.2 3B as the fallback for minimal deployments.
