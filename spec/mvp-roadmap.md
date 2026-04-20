# Prosper0 — MVP Roadmap

**Written:** 2026-04-20  
**MVP Definition:** Ariel can receive a message, call a vault tool, have the call gated by the enforcement chain, and return a response — all logged. The minimum loop that proves the stack works end-to-end.

---

## What MVP Is Not

MVP is not:
- A full vault (Layer 2 complete)
- The Prospero Bridge (Layer 3)
- USB deployment (Layer 6)
- Transparency reports or model comparison harness

MVP is the vertical slice: one conversation, one tool call, one audit log entry, one response.

---

## MVP Milestone Map

### M0 — Foundation (DONE)
Everything needed before the loop can run. Both branches ship together.

| Work | Branch | Status |
|---|---|---|
| Enforcement chain + audit logger | `feature/enforcement-layer` | ✅ 33 tests passing |
| `ModelBackend` interface + `OllamaBackend` | `feature/llm-stack-layer1` | ✅ 8 tests passing |

**Gate:** Both branches merged to main.

---

### M1 — The Loop
The orchestrator loop: system prompt builder + the `while True` agent cycle.

| Component | File | Notes |
|---|---|---|
| `build_system_prompt()` | `stack/orchestrator/prompt.py` | Persona + mode + tool definitions |
| Agent loop | `stack/orchestrator/loop.py` | generate → tool call or final response; max-iteration guard |
| `tools.config.yaml` | `stack/tools.config.yaml` | Operator-written, AI-immutable; loader in `stack/orchestrator/config.py` |

**Ariel's persona is injected here.** The model tag changes; Ariel's identity doesn't.

**Gate:** Loop runs end-to-end with a mocked backend (no Ollama required). Tests cover: text response terminates loop, tool call routes to enforcement chain, max-iteration guard fires.

---

### M2 — First Tool
One real vault tool: `read_file`. Enough for Ariel to answer "what tasks do I have?"

| Component | File | Notes |
|---|---|---|
| `read_file` tool | `stack/mcp/tools/read_file.py` | Path validation; respects vault root; no traversal |
| Tool registry | `stack/mcp/registry.py` | Maps tool name → executor callable |
| Tool definitions | `stack/mcp/definitions.py` | JSON schema for tool passed to Ollama |

**Gate:** Loop + enforcement chain + `read_file` work together. Integration test: "read this vault file" → enforcement gates it → file contents returned → loop continues.

---

### M3 — Ollama Live
Wire real Ollama. Replace the mock backend with a running container.

| Component | File | Notes |
|---|---|---|
| `docker-compose.yml` | `deploy/docker-compose.yml` | Ollama service + prosper0 orchestrator |
| Model pull script | `deploy/pull-model.sh` | `ollama pull qwen2.5:7b` on first run |
| Smoke test | `tests/smoke/test_live.py` | Sends one message, checks for a response; skipped if Ollama not available |

**Gate:** `docker compose up` → send "what tasks do I have?" → Ariel reads vault → response logged to audit trail.

---

### M4 — MVP Complete
The loop is alive, logged, and trustworthy. This is the demo-able state.

**Checklist:**
- [ ] Ariel responds to a free-text message
- [ ] At least one tool call happens in the session
- [ ] Enforcement chain gates the call (authorized path passes, unauthorized path blocks)
- [ ] Audit log captures the full session
- [ ] No employer data leaves the vault automatically
- [ ] `tools.config.yaml` is read-only to the model

---

## Post-MVP Roadmap

Ordered by dependency, not urgency.

| Milestone | Layer | Description |
|---|---|---|
| **P1** — Vault schema | 2 | Define note schemas; port `marlin.py` surfacing engine as `prosper0.py` |
| **P2** — Full tool set | 1 | `write_file`, `list_files`, `search_vault` — CRUD for the vault |
| **P3** — Prospero Bridge | 3 | Context switch protocol; mode propagation from Marlin |
| **P4** — Sample data + boundary tests | 5 | Synthetic vault content; data isolation assertions |
| **P5** — Transparency report | 4 | Human-readable audit report generator |
| **P6** — Model comparison harness | 1 | Same prompt battery across model versions; diffed output |
| **P7** — USB deployment | 6 | Encrypted partition; hardware pairing; desktop shortcut |

---

## Task Index (Marlin)

Tasks tracked in the Marlin vault under `[[Prosper0 — LLM Stack]]` and sub-projects.

| Task | Maps To | Status |
|---|---|---|
| Research and select local LLM | M0 | ✅ Done |
| Design model-agnostic interface | M0 | ✅ Done |
| Build config enforcement | M0 | ✅ Done |
| Build audit trail | M0 | ✅ Done |
| Write tools.config spec | M1 | Open |
| Port surfacing engine | P1 | Open |
| Define vault schema | P1 | Open |
| Build sample data generator | P4 | Open |
| Build model comparison harness | P6 | Open |
| Build transparency report | P5 | Open |
| Build data transfer workflow | P3 | Open |
| Build desktop launcher | P7 | Open |
| Choose encryption approach | P7 | Open |
| Implement clean-break handler | P7 | Open |
| Write data boundary tests | P4 | Open |
| Spec context switch protocol | P3 | Open |
| Design TTF dual-source | P3 | Open |

---

## Current Branch State

| Branch | Contents | Merged? |
|---|---|---|
| `main` | Skeleton + research docs + ADRs | — |
| `feature/enforcement-layer` | Full enforcement chain, 33 tests | ❌ Not yet |
| `feature/llm-stack-layer1` | `ModelBackend` + `OllamaBackend`, 8 tests | ❌ Not yet |

**Next action:** PR both open branches → merge → cut M1 branch.
