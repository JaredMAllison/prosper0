# Tool Use Requirements for Local LLMs

## What Tool Use Actually Is

The model does not execute functions. It generates structured output describing which function to call and what arguments to pass. The orchestrator reads that output, calls the function (through the enforcement chain), and feeds the result back as the next message. The loop continues until the model produces a response with no tool call.

```
Model output: {"tool": "read_vault_file", "args": {"path": "Tasks/task-001.md"}}
                        ↓
              Orchestrator parses tool call
                        ↓
              EnforcementChain.call(tool_name, path, executor)
                        ↓
              Result returned to model as next message
                        ↓
              Model produces next response (text or another tool call)
```

## Two Implementation Approaches

### Native Function Calling (preferred)
The model was trained with tool use as a first-class capability. Tool definitions are passed in a structured schema (OpenAI-compatible JSON). The model reliably emits tool calls in a parseable format. Ollama exposes this via the `/api/chat` endpoint with a `tools` field.

Models with strong native tool use: **Llama 3.2/3.3, Qwen2.5, Mistral** (all support OpenAI-compatible function calling through Ollama).

### Prompt-Engineered Tool Use (fallback)
The model has no native tool calling support. Tool definitions are injected into the system prompt as text. The model is instructed to respond with a specific format when calling a tool. The orchestrator parses free-text output with regex or a small parser. Fragile — format consistency degrades with context length.

**Avoid this if possible.** It makes the orchestrator brittle.

## What to Look for in a Model

| Criterion | Why it matters |
|---|---|
| Native tool calling support | Reliable structured output; parseable by Ollama's API |
| Instruction following | System prompt compliance — modes, persona (Ariel), constraints |
| Context length | Longer context = more vault content + conversation history in the prompt |
| Quantized size (Q4_K_M) | Storage and RAM budget |
| Inference speed (tokens/sec) | Usability — slow responses break the work rhythm |

## Minimum Bar

A model that can't reliably emit valid JSON tool calls makes the orchestrator unreliable. This is the single most important criterion. Everything else is secondary.

## How Tool Definitions Are Passed (Ollama)

```json
{
  "model": "qwen2.5:7b",
  "messages": [...],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "read_vault_file",
        "description": "Read a file from the Prosper0 vault",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {"type": "string", "description": "Vault-relative path"}
          },
          "required": ["path"]
        }
      }
    }
  ]
}
```

Ollama returns a tool call when the model decides to use a tool:

```json
{
  "message": {
    "role": "assistant",
    "tool_calls": [
      {"function": {"name": "read_vault_file", "arguments": {"path": "Tasks/task-001.md"}}}
    ]
  }
}
```

The orchestrator checks `message.tool_calls` — if present, execute through the enforcement chain; if absent, the response is the final answer.

## Conclusion

Require native tool calling support via OpenAI-compatible schema. This is non-negotiable for a reliable orchestrator. All primary candidates (Llama 3.2/3.3, Qwen2.5, Mistral) meet this bar through Ollama.
