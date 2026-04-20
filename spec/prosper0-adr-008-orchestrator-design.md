---
title: "Prosper0-ADR-008: Orchestrator Loop Design"
type: adr
project: Prosper0 — LLM Stack
status: accepted
date: 2026-04-20
tags: [adr, prosper0, llm-stack, orchestrator, architecture]
---

## Context

The orchestrator loop is the layer between the model and everything else. Three design decisions needed to be made explicit before implementation:

1. How does the loop refer to the enforcement chain without creating a hard import dependency on the `transparency` package?
2. What happens when a tool call is rejected or fails mid-loop?
3. What prevents the model from looping forever if it never produces a text response?

## Decisions

### 1. GateCaller Protocol — Decouple loop from enforcement package

The loop defines a `GateCaller` `typing.Protocol` with a single method:

```python
class GateCaller(Protocol):
    def call(self, tool_name, path, executor, is_transfer=False) -> bytes: ...
```

The orchestrator loop imports this protocol. The enforcement chain (`EnforcementChain`) satisfies it structurally — no explicit inheritance required. `main.py` wires the real chain in at startup; tests use `StubGate` or `RejectingGate`.

**Why:** The `transparency` package is Layer 4 code. The orchestrator is Layer 1 code. Layer 1 should not import Layer 4 directly — that creates a hard coupling across layers. The Protocol inverts this: the loop declares what it needs; the enforcement chain provides it.

**Alternative rejected:** Import `EnforcementChain` directly in `loop.py`. Simple, but binds Layer 1 to Layer 4 at import time — any refactor of the transparency package breaks the loop even if the behavior is identical.

### 2. Errors surface as tool results, not exceptions

When `gate.call()` raises (enforcement rejection, executor failure, path traversal), the loop catches the exception and appends the error message as a tool result:

```python
except Exception as exc:
    messages.append({"role": "tool", "content": str(exc)})
```

The model sees the error and responds to it. The loop continues.

**Why:** The model is a reasoning system. If it calls a tool that gets rejected, it should be able to explain the limitation to the operator ("I can't access that path") rather than the whole session crashing. This matches how Claude Code handles tool errors.

**Alternative rejected:** Re-raise and crash. This gives the operator no recovery path within the session and produces a worse user experience.

### 3. Max-iteration guard

The loop accepts a `max_iterations` parameter (default 20). If the model produces `max_iterations` consecutive tool calls without a text response, `MaxIterationsError` is raised.

**Why:** A model that misunderstands the task or gets confused by a tool result can produce an infinite tool-call loop. Without a guard, this burns tokens indefinitely. 20 iterations is generous for any real work task; a model that needs more than 20 tool calls in a row is stuck.

**Alternative rejected:** No guard. Relies on the model always eventually producing text. Not safe.

## Consequences

- The loop is independently testable without the enforcement package present
- `main.py` handles the `ImportError` gracefully with a `_NoOpGate` fallback (dev/test use only — never in production)
- Future alternative enforcement implementations (audit-only mode, test mode) can satisfy `GateCaller` without touching `loop.py`
- The 20-iteration default is configurable per-call for tests that need to trigger the guard with fewer iterations
