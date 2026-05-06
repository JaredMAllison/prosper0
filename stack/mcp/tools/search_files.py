import json
import re
from pathlib import Path

from .read_file import PathTraversalError


def search_files(path: str, pattern: str, vault_root: Path) -> bytes:
    """
    Recursively search files within path for lines matching pattern (regex).
    Returns a JSON array of match objects with 'file', 'line_number', and 'line' fields.
    Raises PathTraversalError if the resolved path escapes the vault root.
    """
    resolved = (vault_root / path.lstrip("/")).resolve()
    if not resolved.is_relative_to(vault_root.resolve()):
        raise PathTraversalError(f"Path '{path}' escapes vault root.")

    target = resolved if resolved.is_dir() else resolved.parent
    regex = re.compile(pattern, re.IGNORECASE)
    matches = []

    files = sorted(target.rglob("*.md")) if resolved.is_dir() else [resolved]
    for file in files:
        if not file.is_file():
            continue
        try:
            for i, line in enumerate(file.read_text(errors="replace").splitlines(), 1):
                if regex.search(line):
                    vault_path = "/" + str(file.resolve().relative_to(vault_root.resolve()))
                    matches.append({
                        "file": vault_path,
                        "line_number": i,
                        "line": line.strip(),
                    })
        except OSError:
            continue

    return json.dumps(matches, indent=2).encode()
