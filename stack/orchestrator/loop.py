from typing import Callable, Optional, Protocol, runtime_checkable

from .backend import ModelBackend

MAX_ITERATIONS = 20


class MaxIterationsError(Exception):
    pass


@runtime_checkable
class GateCaller(Protocol):
    def call(
        self,
        tool_name: str,
        path: Optional[str],
        executor: Callable[[], bytes],
        is_transfer: bool = False,
    ) -> bytes: ...


def run(
    backend: ModelBackend,
    gate: GateCaller,
    tool_executor: Callable[[str, dict], bytes],
    messages: list[dict],
    tools: list[dict],
    system_prompt: str,
    max_iterations: int = MAX_ITERATIONS,
) -> str:
    """
    Agent loop: generate → route tool call through gate → append result → repeat.
    Returns the model's first plain-text response.
    Raises MaxIterationsError if the model never produces a final response.
    """
    messages = list(messages)  # don't mutate caller's list

    for _ in range(max_iterations):
        response = backend.generate(messages, tools, system_prompt)

        if response.is_tool_call:
            tc = response.tool_call
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{"function": {"name": tc.name, "arguments": tc.arguments}}],
            })
            try:
                result = gate.call(
                    tool_name=tc.name,
                    path=tc.arguments.get("path"),
                    executor=lambda: tool_executor(tc.name, tc.arguments),
                )
                messages.append({"role": "tool", "content": result.decode()})
            except Exception as exc:
                # Surface enforcement rejections and executor errors as tool results.
                # The model sees the error and responds to it rather than the loop crashing.
                messages.append({"role": "tool", "content": str(exc)})
        else:
            return response.text

    raise MaxIterationsError(
        f"Agent loop exceeded {max_iterations} iterations without a final response."
    )
