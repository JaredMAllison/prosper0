import fnmatch
from typing import Optional
from transparency.enforcement.config import ToolsConfig


class ToolNotAuthorizedError(Exception):
    pass


class ToolGate:
    def __init__(self, config: ToolsConfig) -> None:
        self._config = config

    def check(self, tool_name: str, path: Optional[str] = None) -> None:
        """Raise ToolNotAuthorizedError if the call is not permitted."""
        # Explicit deny wins over allow
        for rule in self._config.denied_tools:
            if rule.name == tool_name:
                if not rule.paths or self._matches_any(path, rule.paths):
                    raise ToolNotAuthorizedError(
                        f"Tool '{tool_name}' is not authorized for path '{path}'."
                    )

        # Must appear in allow list
        for rule in self._config.allowed_tools:
            if rule.name == tool_name:
                if not rule.paths or self._matches_any(path, rule.paths):
                    return

        raise ToolNotAuthorizedError(
            f"Tool '{tool_name}' is not authorized for path '{path}'."
        )

    def _matches_any(self, path: Optional[str], patterns: list[str]) -> bool:
        if path is None:
            return True
        return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
