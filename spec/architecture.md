# Prosper0 Architecture Reference

A layer-by-layer design reference for the Prosper0 work exobrain.

---

## Founding Principles

See `prosper0-adr-001.md` for the full charter. Summary:

1. **Local inference only.** No cloud API. Model runs on operator-controlled hardware.
2. **Tool immutability.** `stack/tools.config.yaml` is operator-written. The AI cannot modify it.
3. **Employer data sovereignty.** Data never leaves automatically. All transfers are operator-initiated and emailed with the employer CC'd.
4. **Structural transparency.** Every AI tool call is logged. Transparency reports are generated on demand.
5. **Job-incremented versioning.** Prosper0 → Prosper1 → Prosper2. Clean instance per employer.
6. **Naming convention.** `<AI Name> von <Vault Name>`. The vault is Prosper0. The AI's personal name is TBD.

---

## Layer Stack

### Layer 1 — LLM Stack

**Responsibility:** Local inference + tool permission enforcement

The inference runtime hosts a quantized local model. The interface between the orchestrator and the runtime is model-agnostic — a different model can be registered without touching the orchestrator.

`tools.config.yaml` is read at startup and checked before every tool call. The AI has no write access to this file.

**Key files:** `stack/orchestrator/`, `stack/mcp/`, `stack/tools.config.yaml`

---

### Layer 2 — Vault

**Responsibility:** Work-scoped persistent storage + task surfacing

A flat-file markdown vault, fully separate from any personal exobrain. `prosper0.py` surfaces one task at a time; the operator declares mode.

**Key files:** `vault/prosper0.py`, `vault/schema/`

---

### Layer 3 — Prospero Bridge

**Responsibility:** Controlled cross-instance interaction

The bridge manages four signals between Prosper0 and a personal exobrain (e.g., Marlin):

| Signal | Flow | Automatic? |
|---|---|---|
| Context switch | Bidirectional | Operator-triggered |
| TTF calendar push | Both → TTF | Yes (metadata only) |
| Mode propagation | Personal → Prosper0 | Yes (behavioral only) |
| Data transfer | Either direction | No — operator-initiated + email CC |

**Key files:** `bridge/context_switch.py`, `bridge/mode_propagation.py`, `bridge/data_transfer.py`, `bridge/audit_log.py`

---

### Layer 4 — Employer Transparency

**Responsibility:** AI activity audit + data transfer manifest

Config enforcement runs synchronously before every tool call. Audit log entries are written before and after execution. The transparency report reader can audit any time range without technical knowledge.

**Key files:** `transparency/config_enforcement.py`, `transparency/audit_trail.py`, `transparency/report_generator.py`

---

### Layer 5 — Testing Infrastructure

**Responsibility:** Synthetic data + behavioral verification

No real employer data is ever used in tests. The sample data generator produces structurally realistic vault content. Data boundary tests are assertion-based proofs that vault isolation holds under normal and adversarial conditions.

**Key files:** `tests/sample_data/`, `tests/boundary/`, `tests/model_comparison/`

---

### Layer 6 — Portable Deployment

**Responsibility:** Packaging + delivery

Reference deployment: USB drive with encrypted partition, hardware-paired, launched from a desktop shortcut. Other configurations (host-only, hybrid) are supported; see `deploy/README.md` for trade-offs.

**Key files:** `deploy/launch.sh`, `deploy/stop.sh`, `deploy/docker-compose.yml`, `deploy/udev/`

---

## Data Flow

```
Operator
  │
  ├─► Declares mode (Prosper0 modes: available / in-meeting / deep-work / off-hours)
  │
  ├─► Captures to Prosper0 Vault (Inbox → enrich → Tasks / Projects / Decisions)
  │
  ├─► Prosper0.py surfaces one task → Ntfy notification
  │
  ├─► Context switch → Prospero Bridge activates / deactivates
  │
  └─► Data transfer: operator initiates → email drafted → operator sends (employer CC'd) → logged

Personal exobrain (Marlin)
  │
  └─► Mode propagation → Prospero Bridge → Prosper0 behavioral response
      TTF push (personal tasks, source: marlin) → shared calendar view

Prosper0
  │
  └─► TTF push (work tasks, source: prosper0) → shared calendar view
      All tool calls → config enforcement → audit log
```

---

## What Never Happens Automatically

- Personal vault content does not enter Prosper0
- Work vault content does not enter the personal exobrain
- Data does not leave Prosper0 without operator initiation and email send
- The AI cannot modify `tools.config.yaml`
- Mode is never inferred — always operator-declared
