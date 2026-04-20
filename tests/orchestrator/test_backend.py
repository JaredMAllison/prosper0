from stack.orchestrator.backend import ModelBackend, ModelResponse, ToolCall


def test_model_response_is_tool_call_when_tool_call_present():
    response = ModelResponse(text=None, tool_call=ToolCall(name="read_file", arguments={"path": "/vault/Tasks/foo.md"}))
    assert response.is_tool_call is True


def test_model_response_is_not_tool_call_when_text_present():
    response = ModelResponse(text="Here is your answer.", tool_call=None)
    assert response.is_tool_call is False


def test_model_backend_is_abstract():
    """ModelBackend cannot be instantiated directly."""
    import pytest
    with pytest.raises(TypeError):
        ModelBackend()
