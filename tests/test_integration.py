"""
Integration test: loop + registry + read_file wired together.
No Ollama required — StubBackend drives the model responses.
"""
from pathlib import Path

from stack.orchestrator.backend import ModelResponse, ToolCall
from stack.orchestrator.loop import run
from stack.orchestrator.prompt import build_system_prompt
from stack.mcp.registry import make_tool_executor
from stack.mcp.definitions import TOOL_DEFINITIONS


class StubBackend:
    def __init__(self, responses):
        self._responses = iter(responses)

    def generate(self, messages, tools, system_prompt):
        return next(self._responses)

    def list_models(self):
        return []


class PermissiveGate:
    """Passes every call straight through to the executor."""
    def call(self, tool_name, path, executor, is_transfer=False):
        return executor()


def test_loop_reads_vault_file_and_returns_response(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Tasks").mkdir()
    (vault / "Tasks" / "sprint.md").write_text("title: finish M2\nstatus: queued")

    backend = StubBackend([
        ModelResponse(
            text=None,
            tool_call=ToolCall(name="read_file", arguments={"path": "/Tasks/sprint.md"}),
        ),
        ModelResponse(text="You have one task: finish M2.", tool_call=None),
    ])

    system_prompt = build_system_prompt(mode="available", session_id="test-1")
    tool_executor = make_tool_executor(vault_root=vault)
    messages = [{"role": "user", "content": "What tasks do I have?"}]

    result = run(backend, PermissiveGate(), tool_executor, messages, TOOL_DEFINITIONS, system_prompt)

    assert result == "You have one task: finish M2."


def test_loop_surfaces_traversal_error_to_model(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()

    backend = StubBackend([
        ModelResponse(
            text=None,
            tool_call=ToolCall(name="read_file", arguments={"path": "../../etc/passwd"}),
        ),
        ModelResponse(text="I can't access that path.", tool_call=None),
    ])

    system_prompt = build_system_prompt(mode="available", session_id="test-2")
    tool_executor = make_tool_executor(vault_root=vault)
    messages = [{"role": "user", "content": "Read /etc/passwd"}]

    result = run(backend, PermissiveGate(), tool_executor, messages, TOOL_DEFINITIONS, system_prompt)

    assert result == "I can't access that path."
