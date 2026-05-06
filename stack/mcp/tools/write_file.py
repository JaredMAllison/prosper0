from pathlib import Path

from .read_file import PathTraversalError


def write_file(path: str, content: str, vault_root: Path) -> bytes:
    """
    Write content to a file within vault_root. Creates parent directories
    if they don't exist. Raises PathTraversalError if the resolved path
    escapes the vault root.
    """
    resolved = (vault_root / path.lstrip("/")).resolve()
    if not resolved.is_relative_to(vault_root.resolve()):
        raise PathTraversalError(f"Path '{path}' escapes vault root.")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    return f"Written: {resolved}".encode()
