from pathlib import Path


class PathTraversalError(ValueError):
    pass


def read_file(path: str, vault_root: Path) -> bytes:
    """
    Read a file within vault_root. Path is treated as relative to vault_root
    regardless of whether it starts with '/'. Raises PathTraversalError if
    the resolved path escapes the vault root.
    """
    resolved = (vault_root / path.lstrip("/")).resolve()
    if not resolved.is_relative_to(vault_root.resolve()):
        raise PathTraversalError(f"Path '{path}' escapes vault root.")
    return resolved.read_bytes()
