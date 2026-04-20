---
title: "Prosper0-ADR-001: Project Charter"
type: adr
project: Prosper0
status: accepted
date: 2026-04-19
tags: [adr, prosper0, charter, employer-data-sovereignty, portable-deployment]
---

## Context

Prosper0 is the first work-specific LMF instance (see [[lmf-adr-003-virtualization-layer]]). It introduces constraints not present in Marlin:

- The operator works within an employer relationship, which creates data custody obligations
- Work data and personal data must remain isolated even when the same operator uses both
- An employer must be able to verify that the AI system is not exfiltrating data or acting outside sanctioned boundaries
- The deployment target is a transient work environment — not personal hardware the operator fully controls

These constraints require explicit founding decisions that differ from Marlin's personal-sovereignty design.

## Decision

Prosper0 is governed by these founding principles:

**Naming:** The vault is Prosper0. The AI assistant is `[TBD Name] von Prosper0`. The assistant's personal name will be chosen alongside the model selection. Naming follows LMF-ADR-003: `<AI Name> von <Vault Name>`.

**Job-incremented versioning:** Prosper0 is the first instance. When the operator changes employers, the number increments: Prosper0 → Prosper1 → Prosper2. Each job gets a clean instance; the architecture carries forward unchanged.

**Scope isolation:** All data Prosper0 holds is work-scoped. No personal data from Marlin enters Prosper0 automatically or passively. Cross-instance interaction is handled by the Prospero Bridge with explicit operator approval for every transfer.

**LLM stack:** Local inference only. Model not predetermined — model selection is a project deliverable, constrained by the 64GB USB deployment budget. The interface layer is model-agnostic: the model can be swapped without architectural change.

**Tool immutability:** A `tools.config.yaml` file governs which tools and file paths the AI can access. This file is operator-owned and operator-edited only. The AI cannot read, write, or modify it during a session. Every tool call is validated against this config; unauthorized calls are rejected and logged.

**Employer data sovereignty:** Data never leaves Prosper0 automatically. All transfers require operator initiation. When data is transferred, the system drafts an email with the transfer contents; the operator reviews and sends; the email is CC'd to the employer/manager. Every data movement is visible and independently verifiable by the employer.

**Structural transparency:** Every AI tool invocation is logged with timestamp, tool name, input summary, and outcome. A transparency report can be generated on demand for any time range. The employer always has access to a full record of AI activity on their data.

**Portable deployment:** The reference deployment targets a USB drive — the full stack (vault, model weights, Docker image) portable and hardware-paired. The drive is encrypted with a hardware-bound key; physical removal triggers a clean break. Other configurations (vault on host, model on host, hybrid) are valid. Drive size is tracked and optimized as a statistic, not a hard constraint. Setup story for the reference config: hand the drive to someone, place a shortcut on their desktop, done.

## Consequences

- Prosper0 cannot be deployed on employer-controlled cloud infrastructure without violating data sovereignty (the operator would lose control of the hardware key)
- The transparency-via-email mechanism gives the employer an independently verifiable paper trail for every data movement
- Tool immutability means the AI cannot escalate its own privileges; any capability expansion requires the operator to edit the config manually outside of an active session
- Stack size (model + image + vault) is tracked and optimized as a statistic; the USB reference deployment informs model selection trade-offs but does not hard-cap them
- Job-incremented versioning means historical work data is archived per-job, not overwritten
- See also: [[lmf-adr-003-virtualization-layer]], [[Prosper0]]
