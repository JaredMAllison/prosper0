import pytest
from pathlib import Path

from stack.mcp.tools.read_file import read_file, PathTraversalError


def test_reads_file_within_vault(tmp_path):
    (tmp_path / "Tasks").mkdir()
    (tmp_path / "Tasks" / "foo.md").write_bytes(b"title: foo\nstatus: queued")

    result = read_file("/Tasks/foo.md", vault_root=tmp_path)
    assert result == b"title: foo\nstatus: queued"


def test_path_without_leading_slash(tmp_path):
    (tmp_path / "note.md").write_bytes(b"hello")
    assert read_file("note.md", vault_root=tmp_path) == b"hello"


def test_raises_on_traversal(tmp_path):
    with pytest.raises(PathTraversalError):
        read_file("../../etc/passwd", vault_root=tmp_path)


def test_absolute_path_is_treated_as_relative_to_vault(tmp_path):
    # "/etc/passwd" → lstrip("/") → "etc/passwd" → vault_root/etc/passwd
    # This is inside the vault — no traversal. Missing file is a FileNotFoundError, not a security issue.
    with pytest.raises(FileNotFoundError):
        read_file("/etc/passwd", vault_root=tmp_path)


def test_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_file("/Tasks/missing.md", vault_root=tmp_path)


def test_registry_executor_calls_read_file(tmp_path):
    from stack.mcp.registry import make_tool_executor
    (tmp_path / "foo.md").write_bytes(b"content")

    executor = make_tool_executor(vault_root=tmp_path)
    result = executor("read_file", {"path": "/foo.md"})
    assert result == b"content"


def test_registry_raises_on_unknown_tool(tmp_path):
    from stack.mcp.registry import make_tool_executor
    executor = make_tool_executor(vault_root=tmp_path)
    with pytest.raises(ValueError, match="Unknown tool"):
        executor("delete_file", {"path": "/foo.md"})
