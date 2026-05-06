---
title: "Prosper0-ADR-003: Ed25519 Employer-Signed tools.config.yaml"
type: adr
project: Prosper0
status: accepted
date: 2026-04-20
tags: [adr, prosper0, enforcement, cryptography, security]
---

## Context

The claim "the AI cannot modify its own tool permissions" is meaningless without a mechanism enforcing it. Three weaker alternatives were considered:

1. **File permissions alone** — the operator (who runs the container) can change file permissions.
2. **Operator-controlled config** — the operator can edit the file freely; the employer has no cryptographic stake in it.
3. **Honor system** — the AI is instructed not to modify the config. Instructions are not enforcement.

The enforcement layer needed a mechanism that makes tampering structurally detectable without requiring the employer to be online.

## Decision

Two independent enforcement mechanisms, operating at different layers:

**Layer 1 — OS-enforced read-only mount:** `tools.config.yaml` is mounted into the Docker container as read-only. The container cannot write it regardless of permissions, orchestrator behavior, or AI prompting. This is enforced by the container runtime, not by the application.

**Layer 2 — Ed25519 cryptographic signature:** The employer signs `tools.config.yaml` with their private key. The signature file (`.sig`) and the employer's public key (stored separately on the drive) travel with the config. At startup, `ConfigVerifier` verifies the signature before loading the config. Any modification to the file — even a single byte — invalidates the signature. The operator cannot re-sign without the employer's private key.

Ed25519 was chosen over RSA because: keys are 32 bytes (trivial to handle), signatures are 64 bytes, verification is fast, and the `cryptography` library's Ed25519 implementation is mature and well-audited.

## Consequences

**Enables:**
- Employer owns the tool permission set cryptographically, not by policy
- The operator cannot claim ignorance of what permissions were in effect — the signed config is the record
- System fails closed on invalid or missing signature (startup exits, no degraded mode)
- Employer can re-sign a new config to change permissions without operator involvement in the signing step

**Forecloses:**
- Config changes without employer involvement (by design)
- Hot-reloading config during a session (config is loaded once at startup into memory; editing mid-session has no effect)

**Trade-offs:**
- Employer must run a one-time key generation (`signing.py generate`) and sign the config before first use
- If the employer's private key is compromised, an attacker could sign a permissive config — key hygiene is the employer's responsibility
