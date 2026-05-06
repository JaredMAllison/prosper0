# Model-Agnostic Interface Contract

## The Problem

The orchestrator needs to talk to Ollama today. It might talk to a different runtime tomorrow (upgraded Ollama, llama.cpp directly, a future Docker Model Runner). If the orchestrator imports `ollama` directly, every runtime swap touches orchestrator code.

The solution: an abstract `ModelBackend` class. The orchestrator imports the interface. The Ollama adapter implements it. Swapping runtimes means swapping adapters, not rewriting the loop.

---

## The Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class ModelResponse:
    text: Optional[str]       # Final text response (no tool call)
    tool_call: Optional[ToolCall]  # Tool call to execute (no text)

    @property
    def is_tool_call(self) -> bool:
        return self.tool_call is not None


class ModelBackend(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        tools: list[dict],
        system_prompt: str,
    ) -> ModelResponse:
        """Send messages to the model. Return text or a tool call."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return available model identifiers (for version testing harness)."""
```

---

## Ollama Adapter

```python
import httpx
from transparency.enforcement.chain import EnforcementChain


class OllamaBackend(ModelBackend):
    def __init__(self, host: str, model: str) -> None:
        self._host = host
        self._model = model

    def generate(self, messages, tools, system_prompt) -> ModelResponse:
        payload = {
            "model": self._model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "tools": tools,
            "stream": False,
        }
        response = httpx.post(f"{self._host}/api/chat", json=payload)
        response.raise_for_status()
        msg = response.json()["message"]

        if msg.get("tool_calls"):
            tc = msg["tool_calls"][0]["function"]
            return ModelResponse(
                text=None,
                tool_call=ToolCall(name=tc["name"], arguments=tc["arguments"]),
            )
        return ModelResponse(text=msg["content"], tool_call=None)

    def list_models(self) -> list[str]:
        response = httpx.get(f"{self._host}/api/tags")
        response.raise_for_status()
        return [m["name"] for m in response.json()["models"]]
```

---

## How the Orchestrator Uses It

```python
backend = OllamaBackend(host="http://ollama:11434", model="qwen2.5:7b")
chain = EnforcementChain(config=config, audit=audit, ...)

messages = []
system_prompt = build_system_prompt(mode, memory_dir, skills_dir)

while True:
    response = backend.generate(messages, TOOL_DEFINITIONS, system_prompt)

    if response.is_tool_call:
        tc = response.tool_call
        result = chain.call(
            tool_name=tc.name,
            path=tc.arguments.get("path"),
            executor=lambda: execute_tool(tc.name, tc.arguments),
        )
        messages.append({"role": "tool", "content": result.decode()})
    else:
        print(response.text)  # Surface to operator
        break
```

The orchestrator never imports `httpx` or knows about Ollama. It imports `ModelBackend` and `OllamaBackend`. A `LlamaCppBackend` would look identical from the orchestrator's perspective.

---

## Swapping Models

Change one line in config:

```yaml
# config.yaml
model: qwen2.5:7b   # change to qwen2.5:14b, llama3.3:70b, etc.
ollama_host: http://ollama:11434
```

The version testing harness pulls `backend.list_models()`, runs each model against a standard prompt battery, and diffs the outputs. No code changes required to test a new model.

---

## Ariel's Persona in the System Prompt

The model tag changes. Ariel's identity doesn't.

```python
ARIEL_PERSONA = """
You are Ariel, a work assistant running on Prosper0.
You help with task management, project tracking, and knowledge work
within the scope defined by your configuration.

Current mode: {mode}
Session: {session_id}
""".strip()
```

The operator can interact with Ariel regardless of which model is underneath.
