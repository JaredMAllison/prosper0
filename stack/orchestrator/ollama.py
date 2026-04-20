import httpx

from .backend import ModelBackend, ModelResponse, ToolCall


class OllamaBackend(ModelBackend):
    def __init__(self, host: str, model: str) -> None:
        self._host = host
        self._model = model

    def generate(
        self,
        messages: list[dict],
        tools: list[dict],
        system_prompt: str,
    ) -> ModelResponse:
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
