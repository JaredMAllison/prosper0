---
title: "Prosper0-ADR-005: Fail-Closed Throughout the Enforcement Layer"
type: adr
project: Prosper0
status: accepted
date: 2026-04-20
tags: [adr, prosper0, enforcement, reliability, security]
---

## Context

Every enforcement component can fail: the config signature can be invalid, the audit log directory can fill up, the SMTP server can be unreachable. When a component fails, the system has two choices: degrade gracefully (continue without that component) or stop.

Degrading gracefully feels safer to the operator — the AI keeps working. But degraded enforcement is not enforcement. An audit log that silently stops writing is indistinguishable from no audit log. A transfer gate that bypasses SMTP because the server is down has no accountability mechanism.

## Decision

The enforcement layer fails closed at every failure point. When it cannot enforce, it stops. There is no degraded mode.

| Failure | Behavior |
|---|---|
| Config signature invalid at startup | Exit with logged reason — do not start |
| Config file missing at startup | Exit with logged reason — do not start |
| Config malformed (parse error) | Exit — fail closed, never fail open |
| AuditLogger cannot write (disk full, permissions) | Exit — a broken audit trail is a broken guarantee |
| TransferGate SMTP send fails | Transfer does not execute — the email is the gate |
| Tool crashes mid-execution | Pre-entry exists, post-entry absent — gap visible in log |

The implementation raises exceptions (`ConfigVerificationError`, `OSError`) rather than catching and continuing. The orchestrator is responsible for catching these at the top level and terminating the session.

## Consequences

**Enables:**
- The employer can trust that if the system is running, enforcement is active — there is no partial state
- Gaps in the audit log (pre-entry without post-entry) are evidence of unexpected termination, not of silent failure
- The system's reliability guarantees are binary: it enforces, or it stops

**Forecloses:**
- Graceful degradation — the system cannot offer reduced functionality when a component fails
- Operator continuity when infrastructure fails (disk full, SMTP down means work stops)

**Trade-offs:**
- Operationally disruptive: a full disk stops the AI entirely. This is the correct trade-off — the alternative is an AI operating without an audit trail.
- The orchestrator must handle termination cleanly (flush buffers, notify the operator) — this is out of scope for the enforcement layer itself.
