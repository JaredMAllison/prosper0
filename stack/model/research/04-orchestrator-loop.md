# Orchestrator Loop

## What the Orchestrator Does

The orchestrator is the layer between the model and everything else. It:

1. Builds the system prompt (persona + memory + active skill + tool definitions)
2. Manages conversation history
3. Sends messages to Ollama and parses responses
4. Detects tool calls and routes them through the enforcement chain
5. Returns tool results to the model as the next message
6. Loops until the model produces a final text response

The model (Ariel) never directly touches the vault, the audit log, or any external system. Everything goes through the orchestrator → enforcement chain → tool.

---

## The Memory and Skill Layer

This is the local-LLM equivalent of Claude Code's memory files and skills.

**In Claude Code (Marlin):**
- Memory files are auto-loaded into context by the Claude Code runtime
- Skills are invoked via the `Skill` tool, which loads a markdown file and instructs Claude to follow it

**In Ariel (Prosper0):**
- The orchestrator reads memory files from the vault at session start and injects relevant ones into the system prompt
- "Skills" are prompt templates — markdown files the orchestrator loads and includes in the system prompt when a specific mode or task is active
- The model never sees "here is your skill file" as a system feature — it just sees a well-constructed system prompt

```python
# Conceptual system prompt builder
def build_system_prompt(mode: str, memory_dir: Path, skills_dir: Path) -> str:
    parts = [ARIEL_PERSONA]  # "You are Ariel, a work assistant running on Prosper0..."
    parts += load_relevant_memories(memory_dir, mode)
    parts += load_active_skill(skills_dir, mode)
    parts += format_tool_definitions(AVAILABLE_TOOLS)
    return "\n\n".join(parts)
```

---

## The Loop

```
build_system_prompt()
        ↓
Send to Ollama: {system, messages, tools}
        ↓
Parse response
        ↓
  tool_calls present?
  ├── YES → EnforcementChain.call(tool_name, path, executor)
  │           ↓
  │         Append tool result to messages
  │           ↓
  │         Loop back to Send
  └── NO  → Final response → surface to operator
```

**Loop termination:** The model produces a response with no `tool_calls`. Or a max-iteration guard fires (prevents infinite loops if the model gets confused).

**Error handling:** If `EnforcementChain` raises `ToolNotAuthorizedError`, the orchestrator appends an error message to the conversation: `"Tool 'X' is not authorized for path 'Y'."` The model sees this as a tool result and responds accordingly — typically by explaining the limitation to the operator.

---

## Conversation History Management

The full message history is kept in memory for the session. At context limit, the orchestrator trims the oldest non-system messages (sliding window). Memory files and the system prompt are never trimmed — they're injected fresh each turn if needed.

For Qwen2.5 7B with 128K context, trimming is unlikely in normal work sessions. For smaller models (3B, 16K context), the orchestrator needs to be more aggressive.

---

## Mode Awareness

Ariel's behavior changes by mode — the same modes as the vault surfacing engine:
- `available` — full task surface, proactive suggestions
- `in-meeting` — minimal interruption, notes-only mode
- `deep-work` — focused, no unsolicited suggestions
- `off-hours` — silent

Mode is passed to `build_system_prompt()` and changes which skill template is loaded and which memory files are considered relevant.

---

## What This Means for the Interface Contract

The orchestrator needs one thing from the model backend: given a list of messages and a list of tool definitions, return either a text response or a tool call. Everything else (memory, skills, mode, history) is orchestrator responsibility. That's the Q5 interface.
