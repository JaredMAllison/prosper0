---
title: "Prosper0-ADR-004: Self-Certification for Data Transfers"
type: adr
project: Prosper0
status: accepted
date: 2026-04-20
tags: [adr, prosper0, enforcement, transparency, data-transfer]
---

## Context

Data leaving Prosper0 and going to an external destination is the highest-risk action the system can take. Two approaches were considered:

1. **Pre-approval:** The employer must approve each transfer before it executes. This requires the employer to be reachable and responsive. In practice, this means transfers block indefinitely or the operator bypasses the gate.
2. **Post-hoc email CC:** The system sends an email to the employer after the transfer completes. This is transparency, not a control gate — the data has already left before the employer knows.

The goal was low friction for the operator, high accountability for the employer, and no requirement for the employer to be online.

## Decision

Self-certification: the operator certifies the transfer themselves, but the certification is structured so the employer receives full evidence.

The flow:
1. System shows the operator the full transfer content before anything is sent
2. Operator types a reason (minimum 20 characters; the gate loops until the minimum is met)
3. System generates an email draft with: full content, SHA-256 hash, reason, session ID, timestamp
4. Operator sees the exact email preview — what the employer will receive
5. Operator confirms or cancels
6. If confirmed: email is sent to employer, transfer executes, `transfer_complete` is logged with message ID
7. If cancelled: `transfer_cancelled` is logged with content hash; transfer does not execute

Cancelled transfers are logged with the content hash so the employer can see what was *considered* for transfer, not just what was sent.

## Consequences

**Enables:**
- Operator cannot claim ignorance of what was transferred — they previewed it and confirmed the send
- Employer receives full content (not a summary) with a verifiable hash — they can check the log entry matches the email
- No employer availability required — accountability comes from the paper trail, not from real-time approval
- Cancelled transfers are visible — the employer can see what the operator decided not to send

**Forecloses:**
- Automated transfers without operator interaction (by design)
- Bulk transfers that skip the certification flow

**Trade-offs:**
- "Generic responses rejected" (the minimum 20-char rule) is a length gate, not a semantic gate — a determined operator can type 20 meaningless characters. The gate's value is friction and a logged artifact, not guaranteed specificity.
- SMTP send failure blocks the transfer entirely (fail-closed) — if the employer's email is unreachable, the transfer cannot proceed.
