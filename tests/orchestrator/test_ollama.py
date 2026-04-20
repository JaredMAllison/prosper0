import json
import pytest
import httpx

from stack.orchestrator.ollama import OllamaBackend
from stack.orchestrator.backend import ModelResponse, ToolCall


MESSAGES = [{"role": "user", "content": "What tasks are due today?"}]
TOOLS = [{"type": "function", "function": {"name": "read_file", "parameters": {}}}]
SYSTEM = "You are Ariel, a work assistant running on Prosper0."


def _make_response(body: dict) -> httpx.Response:
    return httpx.Response(200, json=body)


def test_generate_returns_text_response(respx_mock):
    respx_mock.post("http://ollama:11434/api/chat").mock(
        return_value=_make_response({"message": {"content": "You have 3 tasks due.", "tool_calls": None}})
    )
    backend = OllamaBackend(host="http://ollama:11434", model="qwen2.5:7b")
    result = backend.generate(MESSAGES, TOOLS, SYSTEM)

    assert isinstance(result, ModelResponse)
    assert result.text == "You have 3 tasks due."
    assert result.tool_call is None
    assert result.is_tool_call is False


def test_generate_returns_tool_call(respx_mock):
    respx_mock.post("http://ollama:11434/api/chat").mock(
        return_value=_make_response({
            "message": {
                "content": None,
                "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": "/vault/Tasks/foo.md"}}}],
            }
        })
    )
    backend = OllamaBackend(host="http://ollama:11434", model="qwen2.5:7b")
    result = backend.generate(MESSAGES, TOOLS, SYSTEM)

    assert result.is_tool_call is True
    assert result.tool_call.name == "read_file"
    assert result.tool_call.arguments == {"path": "/vault/Tasks/foo.md"}
    assert result.text is None


def test_generate_injects_system_prompt(respx_mock):
    """System prompt is prepended as the first message in the payload."""
    captured = {}

    def capture(request):
        captured["body"] = json.loads(request.content)
        return _make_response({"message": {"content": "ok", "tool_calls": None}})

    respx_mock.post("http://ollama:11434/api/chat").mock(side_effect=capture)
    backend = OllamaBackend(host="http://ollama:11434", model="qwen2.5:7b")
    backend.generate(MESSAGES, TOOLS, SYSTEM)

    first_message = captured["body"]["messages"][0]
    assert first_message["role"] == "system"
    assert first_message["content"] == SYSTEM


def test_generate_raises_on_http_error(respx_mock):
    respx_mock.post("http://ollama:11434/api/chat").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    backend = OllamaBackend(host="http://ollama:11434", model="qwen2.5:7b")
    with pytest.raises(httpx.HTTPStatusError):
        backend.generate(MESSAGES, TOOLS, SYSTEM)


def test_list_models(respx_mock):
    respx_mock.get("http://ollama:11434/api/tags").mock(
        return_value=_make_response({"models": [{"name": "qwen2.5:7b"}, {"name": "qwen2.5:14b"}]})
    )
    backend = OllamaBackend(host="http://ollama:11434", model="qwen2.5:7b")
    models = backend.list_models()

    assert models == ["qwen2.5:7b", "qwen2.5:14b"]
