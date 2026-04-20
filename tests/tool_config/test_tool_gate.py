import pytest
from transparency.enforcement.config import ToolsConfig
from transparency.enforcement.tool_gate import ToolGate, ToolNotAuthorizedError


@pytest.fixture
def gate(sample_config_dict):
    config = ToolsConfig.from_dict(sample_config_dict)
    return ToolGate(config)


def test_allowed_tool_with_matching_path(gate):
    gate.check("read_vault_file", "prosper0-vault/Tasks/task.md")  # no exception


def test_allowed_tool_no_path_restriction(gate):
    gate.check("search_vault", None)  # search_vault has no path restriction


def test_denied_path_raises(gate):
    with pytest.raises(ToolNotAuthorizedError) as exc:
        gate.check("read_vault_file", "prosper0-vault/Contacts/client.md")
    assert "not authorized" in str(exc.value)


def test_unknown_tool_raises(gate):
    with pytest.raises(ToolNotAuthorizedError):
        gate.check("delete_vault_file", "prosper0-vault/Tasks/task.md")


def test_allowed_write_to_tasks(gate):
    gate.check("write_vault_file", "prosper0-vault/Tasks/new-task.md")  # no exception


def test_denied_write_outside_allowed_paths(gate):
    with pytest.raises(ToolNotAuthorizedError):
        gate.check("write_vault_file", "prosper0-vault/Projects/secret.md")


def test_error_message_does_not_enumerate_allowed_paths(gate):
    with pytest.raises(ToolNotAuthorizedError) as exc:
        gate.check("read_vault_file", "prosper0-vault/Contacts/client.md")
    # Error must not reveal the full allow-list
    assert "prosper0-vault/**" not in str(exc.value)
    assert "prosper0-vault/Tasks/**" not in str(exc.value)
