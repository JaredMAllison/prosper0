# Tests

Every layer of Prosper0 is independently testable. No real employer data is ever used in tests.

## Structure

```
tests/
├── orchestrator/         ← Unit tests: ModelBackend, OllamaBackend, loop, prompt builder
├── mcp/                  ← Unit tests: read_file tool, registry, path traversal
├── tool_config/          ← Unit tests: enforcement chain, tool gate, audit logger, signing
├── smoke/                ← Live integration tests (auto-skip without Ollama)
├── test_integration.py   ← End-to-end: loop + registry + read_file wired together (no Ollama)
├── boundary/             ← Data isolation assertions (future)
├── bridge/               ← Bridge integration tests (future)
├── model_comparison/     ← Prompt battery + diff harness (future)
└── sample_data/          ← Synthetic vault generator (future)
```

## Running Tests

```bash
# Full suite (excludes live smoke tests)
pytest tests/ --ignore=tests/smoke

# Smoke tests — requires Ollama running at localhost:11434 with qwen2.5:7b pulled
pytest tests/smoke/ -v
```

Smoke tests skip automatically when Ollama is not reachable — CI stays green.

## Test Count

| Suite | Tests | Notes |
|---|---|---|
| `orchestrator/` | 20 | All mocked — no Ollama required |
| `mcp/` | 7 | Filesystem only — no network |
| `tool_config/` | 33 | Enforcement chain full coverage |
| `test_integration.py` | 2 | Loop + read_file end-to-end, mocked backend |
| `smoke/` | 2 | Live — skipped without Ollama |
| **Total (non-smoke)** | **62** | |

## Design Principles

- No real employer data in tests — ever
- Smoke tests are always skippable; CI must pass without Ollama
- Integration tests use real filesystem (`tmp_path`), not mocked I/O
- Enforcement tests treat the chain as a security boundary, not just logic
