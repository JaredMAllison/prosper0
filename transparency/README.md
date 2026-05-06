# Layer 4: Employer Transparency

The structural guarantee that Prosper0 is trustworthy to an employer. Transparency is not a feature added on top — it is the architecture.

## Design Principle

The employer's ability to trust Prosper0 must not depend on trusting the operator's word. The system produces evidence. The architecture makes lying structurally difficult.

## Module Structure

```
transparency/
└── enforcement/
    ├── config.py           ← ToolsConfig dataclass; loads tools.config.yaml
    ├── config_verifier.py  ← Ed25519 signature verification for employer-signed configs
    ├── tool_gate.py        ← Blocks unauthorized tool calls before any I/O
    ├── transfer_gate.py    ← Operator self-certification for data transfers
    ├── audit_logger.py     ← Structured JSONL audit log; one file per day
    ├── signing.py          ← Ed25519 key generation and verification utilities
    └── chain.py            ← Single entry point: gate → executor → audit (atomic)
```

## The Enforcement Chain

Every tool call flows through `EnforcementChain.call()`:

1. `audit_logger.log_attempt()` — logged before anything else
2. `tool_gate.check()` — validates tool name and path against `tools.config.yaml`; raises `ToolNotAuthorizedError` on rejection (logged immediately)
3. `executor()` — the actual tool runs only if the gate passes
4. `audit_logger.log_complete()` — outcome, content hash, byte count logged

No partial execution. If the gate rejects, the executor never runs.

## Audit Log Format

JSONL — one entry per line, one file per day (`audit-YYYY-MM-DD.log`).

```json
{"timestamp": "...", "event": "tool_attempt", "tool": "read_file", "path": "/vault/Tasks/foo.md", "session_id": "abc123"}
{"timestamp": "...", "event": "tool_complete", "tool": "read_file", "path": "/vault/Tasks/foo.md", "outcome": "success", "content_hash": "sha256:...", "bytes": 512, "session_id": "abc123"}
{"timestamp": "...", "event": "tool_rejected", "tool": "write_file", "path": "/etc/passwd", "reason": "path_not_authorized", "session_id": "abc123"}
```

## Config Signing (ADR-003)

`tools.config.yaml` supports an Ed25519 employer signature in the `signed_by` field. If present, `config_verifier.py` verifies it at startup. This gives the employer cryptographic proof that the config they approved is the config that ran.

## ADRs

- [ADR-002](../spec/prosper0-adr-002-enforcement-middleware-chain.md) — Middleware chain pattern
- [ADR-003](../spec/prosper0-adr-003-ed25519-employer-signed-config.md) — Ed25519 signing
- [ADR-004](../spec/prosper0-adr-004-self-certification-transfers.md) — Self-certification for transfers
- [ADR-005](../spec/prosper0-adr-005-fail-closed-enforcement.md) — Fail-closed enforcement
