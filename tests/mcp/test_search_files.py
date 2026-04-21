import json
import pytest
from pathlib import Path

from stack.mcp.tools.search_files import search_files
from stack.mcp.tools.read_file import PathTraversalError


def test_finds_match_in_file(tmp_path):
    (tmp_path / "note.md").write_text("title: Buy milk\nstatus: queued")

    result = json.loads(search_files("/note.md", "buy milk", vault_root=tmp_path))
    assert len(result) == 1
    assert result[0]["line_number"] == 1
    assert result[0]["file"] == "/note.md"


def test_recursive_search_in_directory(tmp_path):
    (tmp_path / "Tasks").mkdir()
    (tmp_path / "Tasks" / "foo.md").write_text("Buy groceries today")
    (tmp_path / "Tasks" / "bar.md").write_text("Call the dentist")

    result = json.loads(search_files("/Tasks/", "groceries", vault_root=tmp_path))
    assert len(result) == 1
    assert "foo.md" in result[0]["file"]


def test_case_insensitive(tmp_path):
    (tmp_path / "note.md").write_text("TITLE: Important Task")

    result = json.loads(search_files("/", "title", vault_root=tmp_path))
    assert len(result) == 1


def test_no_matches_returns_empty(tmp_path):
    (tmp_path / "note.md").write_text("nothing interesting here")

    result = json.loads(search_files("/", "xyzzy", vault_root=tmp_path))
    assert result == []


def test_multiple_matches_in_one_file(tmp_path):
    (tmp_path / "note.md").write_text("foo bar\nbaz\nfoo again")

    result = json.loads(search_files("/note.md", "foo", vault_root=tmp_path))
    assert len(result) == 2
    assert result[0]["line_number"] == 1
    assert result[1]["line_number"] == 3


def test_raises_on_traversal(tmp_path):
    with pytest.raises(PathTraversalError):
        search_files("../../etc", "password", vault_root=tmp_path)


def test_registry_executor_calls_search_files(tmp_path):
    from stack.mcp.registry import make_tool_executor
    (tmp_path / "Tasks").mkdir()
    (tmp_path / "Tasks" / "dentist.md").write_text("Call the dentist tomorrow")

    executor = make_tool_executor(vault_root=tmp_path)
    result = json.loads(executor("search_files", {"path": "/Tasks/", "pattern": "dentist"}))
    assert len(result) == 1
    assert result[0]["line"] == "Call the dentist tomorrow"
