# Layer 1: LLM Stack

The local inference engine for von Prosper0. Model not yet selected — model selection is a project deliverable. The interface is model-agnostic so the model can be swapped without touching the orchestrator.

## Structure

```
stack/
├── model/              ← model config, selection notes, benchmark results
├── mcp/                ← MCP wiring (vault read/write)
├── orchestrator/       ← agent loop
└── tools.config.yaml   ← operator-controlled tool permissions
```

## tools.config.yaml

This file is the operator's declaration of what the AI is allowed to do. It governs which MCP tools, file paths, and capabilities are active. The AI cannot read, write, or modify this file during a session. Every tool call is validated against it before execution.

## Model Selection

Target: local quantized model, capable on reasoning and task management. Primary trade-offs: capability vs. portability size vs. inference speed. See `model/` for evaluation notes and the selection ADR.

## Version Testing

The version testing harness (`tests/model_comparison/`) runs a standard prompt battery against any registered model version and diffs the output. Adding a new model is one config line.
