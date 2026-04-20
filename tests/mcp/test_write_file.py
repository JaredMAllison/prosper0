import pytest
from pathlib import Path

from stack.mcp.tools.read_file import PathTraversalError
from stack.mcp.tools.write_file import write_file


def test_writes_new_file(tmp_path):
    result = write_file("/Tasks/foo.md", "title: foo", vault_root=tmp_path)
    assert (tmp_path / "Tasks" / "foo.md").read_text() == "title: foo"
    assert b"Written" in result


def test_creates_parent_directories(tmp_path):
    write_file("/deep/nested/dir/note.md", "hello", vault_root=tmp_path)
    assert (tmp_path / "deep" / "nested" / "dir" / "note.md").read_text() == "hello"


def test_overwrites_existing_file(tmp_path):
    (tmp_path / "note.md").write_text("old content")
    write_file("/note.md", "new content", vault_root=tmp_path)
    assert (tmp_path / "note.md").read_text() == "new content"


def test_path_without_leading_slash(tmp_path):
    write_file("note.md", "hello", vault_root=tmp_path)
    assert (tmp_path / "note.md").read_text() == "hello"


def test_raises_on_traversal(tmp_path):
    with pytest.raises(PathTraversalError):
        write_file("../../etc/evil.txt", "pwned", vault_root=tmp_path)


def test_absolute_path_rebased_to_vault(tmp_path):
    # "/Tasks/foo.md" → lstrip → "Tasks/foo.md" → vault_root/Tasks/foo.md (safe)
    write_file("/Tasks/foo.md", "content", vault_root=tmp_path)
    assert (tmp_path / "Tasks" / "foo.md").exists()


def test_registry_executor_calls_write_file(tmp_path):
    from stack.mcp.registry import make_tool_executor
    executor = make_tool_executor(vault_root=tmp_path)
    result = executor("write_file", {"path": "/foo.md", "content": "hello"})
    assert (tmp_path / "foo.md").read_text() == "hello"
    assert b"Written" in result
