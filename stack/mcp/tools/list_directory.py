import json
from pathlib import Path

from .read_file import PathTraversalError


def list_directory(path: str, vault_root: Path) -> bytes:
    """
    List the contents of a directory within vault_root. Returns a JSON array
    of entry objects with 'name', 'type' (file|directory), and 'path' fields.
    Raises PathTraversalError if the resolved path escapes the vault root.
    """
    resolved = (vault_root / path.lstrip("/")).resolve()
    if not resolved.is_relative_to(vault_root.resolve()):
        raise PathTraversalError(f"Path '{path}' escapes vault root.")
    if not resolved.is_dir():
        raise ValueError(f"Path '{path}' is not a directory.")

    entries = []
    for entry in sorted(resolved.iterdir()):
        vault_path = "/" + str(entry.resolve().relative_to(vault_root.resolve()))
        entries.append({
            "name": entry.name,
            "type": "directory" if entry.is_dir() else "file",
            "path": vault_path,
        })

    return json.dumps(entries, indent=2).encode()
