from pathlib import Path
from typing import Callable

from .tools.read_file import read_file


def make_tool_executor(vault_root: Path) -> Callable[[str, dict], bytes]:
    """Return a tool executor bound to vault_root."""
    def executor(tool_name: str, arguments: dict) -> bytes:
        if tool_name == "read_file":
            return read_file(arguments["path"], vault_root)
        raise ValueError(f"Unknown tool: '{tool_name}'")
    return executor
