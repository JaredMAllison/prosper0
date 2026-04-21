import json
import pytest
from pathlib import Path

from stack.mcp.tools.list_directory import list_directory
from stack.mcp.tools.read_file import PathTraversalError


def test_lists_files_and_dirs(tmp_path):
    (tmp_path / "Tasks").mkdir()
    (tmp_path / "Tasks" / "foo.md").write_text("hello")
    (tmp_path / "CLAUDE.md").write_text("config")

    result = json.loads(list_directory("/", vault_root=tmp_path))
    names = {e["name"] for e in result}
    assert "Tasks" in names
    assert "CLAUDE.md" in names


def test_entry_types(tmp_path):
    (tmp_path / "Tasks").mkdir()
    (tmp_path / "note.md").write_text("x")

    result = json.loads(list_directory("/", vault_root=tmp_path))
    by_name = {e["name"]: e for e in result}
    assert by_name["Tasks"]["type"] == "directory"
    assert by_name["note.md"]["type"] == "file"


def test_entry_paths_are_vault_relative(tmp_path):
    (tmp_path / "Tasks").mkdir()
    (tmp_path / "Tasks" / "foo.md").write_text("x")

    result = json.loads(list_directory("/Tasks/", vault_root=tmp_path))
    assert result[0]["path"] == "/Tasks/foo.md"


def test_raises_on_traversal(tmp_path):
    with pytest.raises(PathTraversalError):
        list_directory("../../etc", vault_root=tmp_path)


def test_raises_on_non_directory(tmp_path):
    (tmp_path / "note.md").write_text("x")
    with pytest.raises(ValueError, match="not a directory"):
        list_directory("/note.md", vault_root=tmp_path)


def test_registry_executor_calls_list_directory(tmp_path):
    from stack.mcp.registry import make_tool_executor
    (tmp_path / "Tasks").mkdir()
    (tmp_path / "Tasks" / "foo.md").write_text("x")

    executor = make_tool_executor(vault_root=tmp_path)
    result = json.loads(executor("list_directory", {"path": "/Tasks/"}))
    assert result[0]["name"] == "foo.md"
