---
title: "LMF-ADR-003: Virtualization Layer"
type: adr
project: Local Mind Foundation
status: accepted
date: 2026-04-19
tags: [adr, lmf, architecture, virtualization, instances]
---

## Context

LMF-ADR-001 named the Local Mind Foundation as a user-agnostic cognitive prosthetics architecture and established Marlin as the reference instance. As new instances emerge — work-specific exobrains, household shared instances, packaged consumer distributions — a formal model is needed for how the same architecture runs on different substrates with different operators, data scopes, and deployment targets.

Without this model, every new instance risks reinventing its relationship to the core architecture: re-deriving isolation rules, naming conventions, cross-instance protocols, and deployment strategies from scratch.

## Decision

Each LMF instance is defined by three axes:

**1. Scope** — what data the instance holds
- `personal` — the operator's private life, cognition, and history (e.g., Marlin)
- `work` — employer-scoped tasks, projects, and decisions (e.g., Prosper0)
- `household` — shared infrastructure for a community or household (future)
- `packaged` — conversation-only onboarding for users who cannot build their own

**2. Substrate** — where and how the vault persists
- `obsidian-flat-file` — markdown files on operator hardware; human-readable
- `docker-volume` — containerized vault; portable, isolated
- `conversation-only` — no persistent vault; stateful only through the LLM session

**3. Naming** — the AI serving the instance follows the convention `<AI Name> von <Instance Name>`
- The vault has a proper noun name (Marlin, Prosper0)
- The AI has a personal name chosen by the operator
- "von" is the connector: Claude von Marlin; [Name] von Prosper0
- The name is operator-chosen, not inherited from the model vendor

**Instance isolation is the default.** Data does not flow automatically between instances. Cross-instance interaction requires an explicit bridge layer with operator-approved transfer protocols.

Each instance registers itself with:
- `instance_name` — proper noun (e.g., Marlin, Prosper0)
- `scope` — personal | work | household | packaged
- `substrate` — obsidian-flat-file | docker-volume | conversation-only
- `ai_name` — full `<Name> von <Instance>` designation when chosen
- `operator` — who owns and controls the instance

## Consequences

- Prosper0 is the first non-personal instance: scope `work`, substrate `docker-volume`, operator Jared Allison
- The Prospero Bridge becomes the canonical cross-instance protocol — constrained by this model (no automatic flows; explicit operator approval for all data transfers)
- Future household and packaged instances have a clear registration model to build against
- The `<Name> von <Instance>` convention is now the LMF standard for all instances
- The LMF profile document (`LOCAL_MIND_FOUNDATION.md`) is scoped to a single instance; multi-instance operators maintain one profile per instance
