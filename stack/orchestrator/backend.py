from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class ModelResponse:
    text: Optional[str]
    tool_call: Optional[ToolCall]

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
        """Return available model identifiers."""
