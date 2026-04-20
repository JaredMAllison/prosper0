import pytest

from stack.orchestrator.backend import ModelBackend, ModelResponse, ToolCall
from stack.orchestrator.loop import run, MaxIterationsError, GateCaller


TOOLS = [{"type": "function", "function": {"name": "read_file"}}]
SYSTEM = "You are Ariel."
MESSAGES = [{"role": "user", "content": "What tasks do I have?"}]


class StubBackend(ModelBackend):
    """Returns responses from a queue."""
    def __init__(self, responses: list[ModelResponse]):
        self._queue = list(responses)

    def generate(self, messages, tools, system_prompt) -> ModelResponse:
        return self._queue.pop(0)

    def list_models(self) -> list[str]:
        return []


class StubGate:
    """Permissive gate — always allows, returns result bytes."""
    def __init__(self, result: bytes = b"file contents"):
        self.calls = []
        self._result = result

    def call(self, tool_name, path, executor, is_transfer=False) -> bytes:
        self.calls.append((tool_name, path))
        return executor()


class RejectingGate:
    """Always raises on call."""
    def call(self, tool_name, path, executor, is_transfer=False) -> bytes:
        raise PermissionError(f"Tool '{tool_name}' not authorized.")


def make_tool_executor(result: bytes = b"vault content"):
    def executor(tool_name: str, arguments: dict) -> bytes:
        return result
    return executor


def test_text_response_terminates_loop():
    backend = StubBackend([ModelResponse(text="You have 3 tasks.", tool_call=None)])
    gate = StubGate()
    result = run(backend, gate, make_tool_executor(), MESSAGES, TOOLS, SYSTEM)
    assert result == "You have 3 tasks."
    assert gate.calls == []  # no tool calls made


def test_tool_call_routes_through_gate_then_returns_text():
    backend = StubBackend([
        ModelResponse(text=None, tool_call=ToolCall(name="read_file", arguments={"path": "/vault/Tasks/foo.md"})),
        ModelResponse(text="You have 1 task: foo.", tool_call=None),
    ])
    gate = StubGate(result=b"title: foo\nstatus: queued")
    result = run(backend, gate, make_tool_executor(b"title: foo\nstatus: queued"), MESSAGES, TOOLS, SYSTEM)

    assert result == "You have 1 task: foo."
    assert gate.calls == [("read_file", "/vault/Tasks/foo.md")]


def test_enforcement_rejection_surfaces_as_tool_result():
    """A rejected tool call becomes an error message in the conversation; loop continues."""
    backend = StubBackend([
        ModelResponse(text=None, tool_call=ToolCall(name="read_file", arguments={"path": "/etc/passwd"})),
        ModelResponse(text="I can't access that path.", tool_call=None),
    ])
    result = run(backend, RejectingGate(), make_tool_executor(), MESSAGES, TOOLS, SYSTEM)
    assert result == "I can't access that path."


def test_max_iterations_guard_fires():
    """Loop raises MaxIterationsError if the model never produces a text response."""
    tool_call = ModelResponse(
        text=None,
        tool_call=ToolCall(name="read_file", arguments={"path": "/vault/Tasks/foo.md"}),
    )
    backend = StubBackend([tool_call] * 5)
    # Refill queue after exhaustion by making generate always return tool_call
    backend._queue = None
    backend.generate = lambda *_: tool_call

    with pytest.raises(MaxIterationsError):
        run(backend, StubGate(), make_tool_executor(), MESSAGES, TOOLS, SYSTEM, max_iterations=5)


def test_caller_messages_not_mutated():
    """run() must not modify the caller's message list."""
    backend = StubBackend([ModelResponse(text="Done.", tool_call=None)])
    original = list(MESSAGES)
    run(backend, StubGate(), make_tool_executor(), MESSAGES, TOOLS, SYSTEM)
    assert MESSAGES == original


def test_gate_caller_protocol_satisfied_by_stub():
    assert isinstance(StubGate(), GateCaller)
