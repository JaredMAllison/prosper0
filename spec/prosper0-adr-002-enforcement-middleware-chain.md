---
title: "Prosper0-ADR-002: Enforcement Layer as Middleware Chain"
type: adr
project: Prosper0
status: accepted
date: 2026-04-20
tags: [adr, prosper0, enforcement, architecture]
---

## Context

The enforcement layer needs to authorize tool calls, log them, and handle data transfers — and it needs to do this for every tool call, regardless of which LLM or orchestrator is running. The naive approach is to put these checks inline in each tool implementation. That approach fails when tools are added, swapped, or run by different orchestrators: enforcement becomes optional, duplicated, and easy to miss.

## Decision

Implement enforcement as a sequential middleware chain with a single entry point (`EnforcementChain.call`). Every tool call passes through the same chain in this order:

1. `AuditLogger PRE` — log the attempt before anything executes
2. `ToolGate` — authorize or reject; rejected calls never reach the executor
3. Tool executes (if authorized)
4. `TransferGate` — self-certification (transfer calls only)
5. `AuditLogger POST` — log the outcome with content hash

The orchestrator calls `chain.call(tool_name, path, executor, is_transfer)` and the chain handles the rest. The executor function is only called if authorization passes.

## Consequences

**Enables:**
- Stack-agnostic enforcement: any LLM, any orchestrator, same chain
- Unauthorized calls never partially execute — rejection happens before the executor is called
- A crash between PRE and POST is structurally visible in the log (pre-entry present, post-entry absent)
- Adding a new enforcement step means adding it once to the chain, not to every tool

**Forecloses:**
- Per-tool customization of enforcement order (all tools follow the same chain)
- Async tool execution without redesigning the chain interface

**Trade-offs:**
- The chain is synchronous; the TransferGate blocks on operator input. This is intentional — transfers require human confirmation and should not be non-blocking.
