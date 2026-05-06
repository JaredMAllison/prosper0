# Layer 3: Prospero Bridge

The controlled interface between a personal exobrain (e.g., Marlin) and Prosper0. The bridge is a protocol, not a pipe — its job is to prevent collapse, not enable free flow.

## What Crosses

| Signal | Direction | Automatic? |
|---|---|---|
| Context switch (active instance) | Both | Yes — operator action triggers it |
| TTF task visibility | Both → TTF | Yes — each vault pushes with `source:` tag |
| Mode propagation | Personal → Prosper0 | Yes — behavioral response only, no data |
| Data transfer | Either direction | No — operator-initiated, email CC'd to employer/manager |

## Files

- `context_switch.py` — active instance declaration protocol
- `mode_propagation.py` — personal mode change → Prosper0 behavioral response
- `data_transfer.py` — operator-initiated transfer flow with email draft
- `audit_log.py` — structured log of all bridge events

## Data Transfer Flow

1. Operator declares intent to transfer data
2. System identifies content, drafts email with full contents
3. Operator reviews draft
4. Operator sends — employer/manager is CC'd
5. System logs: content hash, destination, timestamp, email message ID

Nothing moves without the operator pressing send.
