# Layer 2: Vault

A work-scoped flat-file vault (markdown). Fully separate from any personal exobrain. No shared directories, no passive data flow between instances.

## Structure

```
vault/
├── schema/     ← frontmatter specs and note templates for each type
└── prosper0.py ← surfacing engine
```

## Note Types

| Type | Purpose |
|---|---|
| Tasks | Work items surfaced one at a time |
| Projects | Work-scoped project tracking |
| Decisions | ADRs and work decisions |
| Contacts | Work contacts and context |
| Daily | Work journal entries |
| Inbox | Verbatim capture buffer |

## Surfacing Engine

`prosper0.py` mirrors `marlin.py` from the Marlin personal exobrain. One task at a time. Operator-declared mode governs what surfaces.

**Work modes:** `available` · `in-meeting` · `deep-work` · `off-hours`

Mode is always operator-declared — never inferred.
