from pathlib import Path
from typing import Callable

from .tools.list_directory import list_directory
from .tools.read_file import read_file
from .tools.search_files import search_files
from .tools.write_file import write_file


def make_tool_executor(vault_root: Path) -> Callable[[str, dict], bytes]:
    """Return a tool executor bound to vault_root."""
    def executor(tool_name: str, arguments: dict) -> bytes:
        if tool_name == "search_files":
            return search_files(arguments["path"], arguments["pattern"], vault_root)
        if tool_name == "list_directory":
            return list_directory(arguments["path"], vault_root)
        if tool_name == "read_file":
            return read_file(arguments["path"], vault_root)
        if tool_name == "write_file":
            return write_file(arguments["path"], arguments["content"], vault_root)
        raise ValueError(f"Unknown tool: '{tool_name}'")
    return executor
