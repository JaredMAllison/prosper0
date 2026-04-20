# Prosper0

A work-specific exobrain — a locally-sovereign AI assistant scoped entirely to a single employer relationship. Built on the [Local Mind Foundation](https://github.com/local-mind-foundation) architecture.

When the job changes, the number increments: Prosper0 → Prosper1 → Prosper2. The architecture carries forward. The vault stays archived.

---

## Why This Exists

Most AI productivity tools are designed for individual optimization inside a trust relationship that doesn't exist: the employer trusts the AI, the employee trusts the vendor, and no one has a clear answer for where the data goes.

Prosper0 takes a different position:

- **The operator owns the hardware.** The stack runs locally — no cloud, no vendor data custody.
- **The employer can verify everything.** Every AI action is logged. Every data transfer is emailed with the employer CC'd. The employer has a paper trail they didn't have to ask for.
- **The AI cannot expand its own permissions.** Tool access is controlled by a config file the AI cannot write. Any capability expansion requires the operator to edit the config manually.

This isn't a productivity tool. It's a trust architecture.

---

## Architecture

Six layers, each independently testable:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 6: Portable Deployment                           │
│  Encrypted USB drive · Hardware-drive pairing ·         │
│  Single desktop shortcut = entire setup                 │
├─────────────────────────────────────────────────────────┤
│  Layer 5: Testing Infrastructure                        │
│  Sample data generator · Model version comparison ·     │
│  Bridge integration tests · Data boundary tests         │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Employer Transparency                         │
│  AI-immutable tool config · Audit trail ·               │
│  Data transfer manifest · Transparency reports          │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Prospero Bridge                               │
│  Context switching · Shared TTF calendar ·              │
│  Mode propagation · Email-CC'd data transfer            │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Prosper0 Vault                                │
│  Work-scoped flat-file vault · Surfacing engine ·       │
│  Webhook handler · Work modes                           │
├─────────────────────────────────────────────────────────┤
│  Layer 1: LLM Stack (von Prosper0)                      │
│  Local inference · Model-agnostic interface ·           │
│  MCP wiring · Orchestrator · Tool config                │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: LLM Stack

The AI brain for the work instance. Local inference only — no cloud API. The inference layer is model-agnostic: swap the model without touching the orchestrator.

- `stack/tools.config.yaml` — operator-controlled tool permissions; the AI cannot write this file
- Model selection is an open deliverable; the interface contract is designed first
- Version testing harness: run the same prompt battery across model versions and diff the output

See: [`stack/README.md`](stack/README.md)

---

## Layer 2: Vault

A work-scoped flat-file vault (markdown). Fully separate from any personal exobrain — no shared directories, no passive data flow. Mirrors [Marlin](https://github.com/local-mind-foundation/marlin) patterns but scoped to work context.

- `prosper0.py` — surfacing engine (one work task at a time, operator-declared mode)
- Work-specific modes: `available` · `in-meeting` · `deep-work` · `off-hours`

See: [`vault/README.md`](vault/README.md)

---

## Layer 3: Prospero Bridge

The controlled interface between the personal exobrain (Marlin) and the work instance (Prosper0). No data flows automatically. Every crossing is explicit, operator-initiated, and logged.

- Context switch signal (which instance is active)
- Shared TTF calendar view (both vaults push tasks with a `source:` tag; calendar renders both without cross-contaminating vault content)
- Mode propagation (Marlin mode change → Prosper0 behavioral response)
- Data transfer: operator initiates → system drafts email → operator sends with employer CC'd → system logs

See: [`bridge/README.md`](bridge/README.md)

---

## Layer 4: Employer Transparency

The structural guarantee that Prosper0 is trustworthy to an employer.

- `tools.config.yaml` defines all AI tool access; human-editable only
- Every AI tool invocation is logged before and after execution
- Every approved data transfer is logged with content hash, destination, and email message ID
- Transparency report generator produces human-readable summaries for any time range

See: [`transparency/README.md`](transparency/README.md)

---

## Layer 5: Testing Infrastructure

Every layer is independently testable. No real employer data is ever used in tests.

- Sample data generator: realistic synthetic vault content
- Model version comparison harness: capability regression testing across model upgrades
- Bridge integration tests: end-to-end context switching and transfer flows
- Data boundary tests: assertion-based proof that vault isolation holds

See: [`tests/README.md`](tests/README.md)

---

## Layer 6: Portable Deployment

The full stack runs from a USB drive. The reference deployment story: hand someone the drive, ask to put a shortcut on their desktop, done. The drive is encrypted and hardware-paired — physically removing it ends the session cleanly.

Deployment configurations are flexible: vault on host, model on host, or everything on the drive. Size is tracked and optimized as a project statistic.

See: [`deploy/README.md`](deploy/README.md)

---

## Design Decisions

See [`spec/`](spec/) for architecture decision records:

- [`spec/lmf-adr-003.md`](spec/lmf-adr-003.md) — LMF Virtualization Layer (how Prosper0 relates to the broader architecture)
- [`spec/prosper0-adr-001.md`](spec/prosper0-adr-001.md) — Project Charter (founding principles)
- [`spec/architecture.md`](spec/architecture.md) — layer-by-layer design reference

---

## Status

Active development. Layer 1 (model selection) is the current priority.

Built by Jared Allison. Part of the [Local Mind Foundation](https://github.com/local-mind-foundation) project.
