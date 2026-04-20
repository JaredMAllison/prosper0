# Enforcement Layer Design

**Date:** 2026-04-19  
**Status:** Approved  
**Scope:** Layer 4 — Employer Transparency (enforcement components)

---

## Problem

Three enforcement gaps identified in the initial architecture review:

1. "AI cannot modify tools.config.yaml" was a claim, not a mechanism
2. "Email CC'd to employer" was transparency after the fact, not a control gate
3. "Input summary" in the audit log contradicted the "full record" promise

This design closes all three with stack-agnostic mechanisms that work regardless of which LLM or inference runtime is chosen.

---

## Architecture

A middleware chain. Every tool call passes through it in sequence. No tool executes without passing all gates.

```
Orchestrator wants to call a tool
        │
        ▼
  ┌─────────────┐
  │ConfigVerifier│  ← Startup only. Verifies employer signature on
  └─────────────┘    tools.config.yaml. Exits if invalid.
        │
        ▼
  ┌──────────┐
  │ ToolGate │  ← Every call. Checks tool name + path against
  └──────────┘    loaded config. Rejects before any execution.
        │
        ▼
  AuditLogger PRE  ← Logs the attempt before anything executes
        │
        ▼
  ┌──────────────┐
  │ TransferGate │  ← Transfer calls only. Self-certification flow.
  └──────────────┘    Blocks until operator sends email to employer.
        │
        ▼
   Tool executes
        │
        ▼
  AuditLogger POST ← Logs outcome + content hash after execution
```

**Ordering rationale:**
- ToolGate rejects before any execution — unauthorized calls never partially run
- AuditLogger pre-entry fires after authorization but before execution — a crash between pre and post is visible
- TransferGate runs between pre and post — the email send is logged, transfer doesn't execute until it succeeds
- AuditLogger post-entry is the last thing that runs — outcome and hash are always final state

---

## Component 1: ConfigVerifier

Runs once at startup. Failure exits the system — no fallback, no degraded mode.

### What it does

1. Reads `tools.config.yaml` from the read-only Docker mount
2. Reads the employer's public key (stored separately on the drive, outside the container)
3. Verifies the config file's cryptographic signature against the public key
4. If valid: loads config into memory, makes it available to ToolGate
5. If invalid or missing: logs the failure with reason, exits non-zero

### Config file format

```yaml
version: 1
signed_by: employer@company.com
tools:
  allowed:
    - name: read_vault_file
      paths: ["prosper0-vault/**"]
    - name: write_vault_file
      paths: ["prosper0-vault/Tasks/**", "prosper0-vault/Inbox.md"]
    - name: search_vault
  denied:
    - name: read_vault_file
      paths: ["prosper0-vault/Contacts/**"]
transfer:
  allowed: true
  max_size_kb: 50
  employer_email: employer@company.com
```

### Enforcement mechanism

`tools.config.yaml` is mounted read-only into the Docker container. The container cannot write it regardless of permissions, orchestrator behavior, or AI prompting. This is OS-enforced at the container level.

The employer signs the config with their private key. The operator cannot modify the file without invalidating the signature, and cannot re-sign without the employer's private key. The employer owns the canonical version cryptographically.

**Signing flow (employer side):** One command against the config file produces a `.sig` file alongside it. Both live on the drive.

The config is loaded into memory at startup and never re-read during a session. Editing the file mid-session has no effect.

---

## Component 2: ToolGate

Runs on every tool call, synchronously, before any execution.

### What it does

1. Receives tool name + parameters from the orchestrator
2. Looks up the tool name in the in-memory config
3. If the tool has path restrictions: checks the requested path against allowed patterns
4. If authorized: passes through to TransferGate / AuditLogger / execution
5. If denied: logs a rejection entry and returns an error to the orchestrator

### What the AI sees on rejection

```
Tool 'read_vault_file' is not authorized for path 'prosper0-vault/Contacts/client.md'.
```

The error does not enumerate which paths are allowed. The AI cannot determine the allow-list from rejections alone.

### What ToolGate does not do

It does not interpret the AI's intent. It checks the call against the config. That is the full scope of its responsibility.

---

## Component 3: TransferGate

Runs only on transfer-type tool calls. Blocks execution until the operator completes self-certification.

### Self-certification flow

```
1. System renders full transfer content for operator review
2. System prompts: "Reason for transfer:" (min 20 chars; generic responses rejected)
3. Operator types reason
4. System generates email draft:
     To: [employer_email from config]
     Subject: [Date] Data Transfer — [first 60 chars of reason]
     Body:
       Reason: [full reason]
       Content: [full transfer content]
       Content hash: sha256:[hash]
       Session: [session_id]
       Timestamp: [ISO 8601]
5. System shows full email preview — operator sees exactly what employer will receive
6. Operator confirms send or cancels
7. If confirmed: system sends via configured SMTP, logs message ID, transfer executes
8. If cancelled: system logs cancellation including content hash, transfer does not execute
```

### What this guarantees

- Operator read the content before it was sent (preview is mandatory)
- Operator provided a reason (logged + included in email)
- Employer received the full content, not a summary
- Employer can verify content integrity (hash in email matches hash in log)
- Cancelled transfers are also logged — employer can see what was considered for transfer

### Design rationale

This is self-certification, not employer pre-approval. The employer does not need to be online or responsive. Accountability comes from the paper trail: the operator cannot claim ignorance of what was sent, and the employer has independently verifiable evidence of every transfer.

---

## Component 4: AuditLogger

Runs on every tool call — twice. Pre-execution and post-execution.

### Log entries

**Attempt (pre-execution):**
```json
{
  "timestamp": "2026-04-19T20:33:00Z",
  "event": "tool_attempt",
  "tool": "read_vault_file",
  "path": "prosper0-vault/Tasks/task-001.md",
  "session_id": "prosper0-2026-04-19-1"
}
```

**Completion (post-execution):**
```json
{
  "timestamp": "2026-04-19T20:33:01Z",
  "event": "tool_complete",
  "tool": "read_vault_file",
  "path": "prosper0-vault/Tasks/task-001.md",
  "outcome": "success",
  "content_hash": "sha256:a3f8c2...",
  "bytes": 1240,
  "session_id": "prosper0-2026-04-19-1"
}
```

**Rejection (ToolGate denial):**
```json
{
  "timestamp": "2026-04-19T20:33:00Z",
  "event": "tool_rejected",
  "tool": "read_vault_file",
  "path": "prosper0-vault/Contacts/client.md",
  "reason": "path_not_authorized",
  "session_id": "prosper0-2026-04-19-1"
}
```

**Transfer cancelled:**
```json
{
  "timestamp": "2026-04-19T20:33:00Z",
  "event": "transfer_cancelled",
  "content_hash": "sha256:...",
  "operator_confirmed": false,
  "session_id": "prosper0-2026-04-19-1"
}
```

### Format and storage

- One JSON object per line, append-only
- Daily rotating files: `audit-YYYY-MM-DD.log`
- Append-only enforced by file permissions — no process has write access beyond appending
- Lives on the drive alongside the vault

### Content hash

SHA-256 of the exact bytes read or written. The employer can verify: hash the file at that path, compare to the log entry. If it matches, the log accurately reflects what was accessed at that moment.

### Gap detection

A pre-entry with no matching post-entry means something interrupted execution. The transparency report flags these gaps explicitly.

---

## Failure Modes

The rule throughout: **fail closed**. When the enforcement layer cannot enforce, it stops. It never degrades to "enforcement optional."

| Failure | Behavior |
|---|---|
| Config signature invalid at startup | Exit, log reason, do not start |
| Config file missing at startup | Exit, log reason, do not start |
| Config malformed (parse error) | Exit — fail closed, never fail open |
| AuditLogger cannot write (disk full, permissions) | Exit — a broken audit trail is a broken guarantee |
| TransferGate SMTP send fails | Transfer does not execute — the email is the gate |
| Tool crashes mid-execution | Pre-entry exists, post-entry absent — gap visible in log |
| Drive removed mid-session | Container I/O errors, session terminates — gaps mark the boundary |

---

## What the Employer Has

- **Cryptographic control** over what the AI is allowed to do (signed config, read-only mount)
- **Complete append-only record** of everything it did (audit log, pre+post entries)
- **Full content** of everything that left the system (transfer email + hash)
- **Evidence of intent** for every transfer (typed reason, preview confirmation)
- **Visibility into cancelled transfers** (what was considered but not sent)

---

## Out of Scope

- Model selection and inference runtime (enforcement layer is LLM-stack-agnostic)
- Vault schema and surfacing engine (Layer 2)
- Bridge protocol between Marlin and Prosper0 (Layer 3)
- Deployment encryption and hardware pairing (Layer 6)
