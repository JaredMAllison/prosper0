"""
Live smoke test — requires a running Ollama instance.
Skipped automatically when Ollama is not reachable.

Run manually: pytest tests/smoke/ -v
"""
import pytest
import httpx

from stack.orchestrator.ollama import OllamaBackend
from stack.orchestrator.prompt import build_system_prompt
from stack.orchestrator.loop import run
from stack.mcp.registry import make_tool_executor
from stack.mcp.definitions import TOOL_DEFINITIONS


OLLAMA_HOST = "http://localhost:11434"
MODEL = "qwen2.5:7b"


def ollama_available() -> bool:
    try:
        r = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def model_available() -> bool:
    try:
        r = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        return any(MODEL in m for m in models)
    except Exception:
        return False


skip_no_ollama = pytest.mark.skipif(
    not ollama_available(),
    reason="Ollama not reachable at localhost:11434",
)

skip_no_model = pytest.mark.skipif(
    not model_available(),
    reason=f"Model {MODEL} not pulled in Ollama",
)


class PermissiveGate:
    def call(self, tool_name, path, executor, is_transfer=False):
        return executor()


@skip_no_ollama
@skip_no_model
def test_ariel_returns_a_response(tmp_path):
    """Ariel produces a non-empty text response to a simple greeting."""
    backend = OllamaBackend(host=OLLAMA_HOST, model=MODEL)
    system_prompt = build_system_prompt(mode="available", session_id="smoke-1")
    tool_executor = make_tool_executor(vault_root=tmp_path)
    messages = [{"role": "user", "content": "Hello. What is your name?"}]

    result = run(backend, PermissiveGate(), tool_executor, messages, TOOL_DEFINITIONS, system_prompt)

    assert isinstance(result, str)
    assert len(result) > 0


@skip_no_ollama
@skip_no_model
def test_ariel_reads_vault_file(tmp_path):
    """Ariel uses read_file to answer a question about vault content."""
    (tmp_path / "Tasks").mkdir()
    (tmp_path / "Tasks" / "test-task.md").write_text(
        "---\ntitle: Deploy Ariel\nstatus: queued\n---\nGet Ariel running on employer hardware."
    )

    backend = OllamaBackend(host=OLLAMA_HOST, model=MODEL)
    system_prompt = build_system_prompt(mode="available", session_id="smoke-2")
    tool_executor = make_tool_executor(vault_root=tmp_path)
    messages = [{"role": "user", "content": "Read /Tasks/test-task.md and summarize it."}]

    result = run(backend, PermissiveGate(), tool_executor, messages, TOOL_DEFINITIONS, system_prompt)

    assert isinstance(result, str)
    assert len(result) > 0
