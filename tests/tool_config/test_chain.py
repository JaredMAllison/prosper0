import json
import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch
from transparency.enforcement.config import ToolsConfig
from transparency.enforcement.audit_logger import AuditLogger
from transparency.enforcement.chain import EnforcementChain
from transparency.enforcement.tool_gate import ToolNotAuthorizedError
from transparency.enforcement.transfer_gate import TransferCancelledError


@pytest.fixture
def chain(sample_config_dict, tmp_path):
    config = ToolsConfig.from_dict(sample_config_dict)
    audit = AuditLogger(log_dir=tmp_path / "logs")
    return EnforcementChain(
        config=config,
        audit=audit,
        smtp_config={"host": "localhost", "port": 25, "from_addr": "test@local"},
        session_id="test-session",
        log_dir=tmp_path / "logs",
    )


def _entries(tmp_path):
    logs = list((tmp_path / "logs").glob("audit-*.log"))
    return [json.loads(l) for l in logs[0].read_text().strip().splitlines()]


def test_authorized_call_executes_and_logs(chain, tmp_path):
    content = b"task content"
    result = chain.call(
        tool_name="read_vault_file",
        path="prosper0-vault/Tasks/task.md",
        executor=lambda: content,
    )
    assert result == content
    entries = _entries(tmp_path)
    assert entries[0]["event"] == "tool_attempt"
    assert entries[1]["event"] == "tool_complete"
    expected_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
    assert entries[1]["content_hash"] == expected_hash


def test_rejected_call_logs_and_raises(chain, tmp_path):
    with pytest.raises(ToolNotAuthorizedError):
        chain.call(
            tool_name="read_vault_file",
            path="prosper0-vault/Contacts/secret.md",
            executor=lambda: b"should not run",
        )
    entries = _entries(tmp_path)
    assert entries[0]["event"] == "tool_attempt"
    assert entries[1]["event"] == "tool_rejected"
    assert entries[1]["reason"] == "path_not_authorized"


def test_executor_not_called_when_rejected(chain):
    called = []
    def executor():
        called.append(True)
        return b"data"
    with pytest.raises(ToolNotAuthorizedError):
        chain.call(
            tool_name="read_vault_file",
            path="prosper0-vault/Contacts/secret.md",
            executor=executor,
        )
    assert called == [], "executor must not be called on rejected calls"


def test_transfer_call_runs_certify(chain, tmp_path):
    content = b"project status report"
    with patch("builtins.input", side_effect=["sharing project status with manager for review", "yes"]):
        with patch.object(chain._transfer_gate, "_send_email", return_value="<msg-id@smtp>"):
            result = chain.call(
                tool_name="transfer_data",
                path=None,
                executor=lambda: content,
                is_transfer=True,
            )
    assert result == content
    entries = _entries(tmp_path)
    events = [e["event"] for e in entries]
    assert "tool_attempt" in events
    assert "transfer_complete" in events
    assert "tool_complete" in events


def test_cancelled_transfer_does_not_complete(chain, tmp_path):
    with patch("builtins.input", side_effect=["sharing status update with manager for review", "no"]):
        with pytest.raises(TransferCancelledError):
            chain.call(
                tool_name="transfer_data",
                path=None,
                executor=lambda: b"content",
                is_transfer=True,
            )
    entries = _entries(tmp_path)
    events = [e["event"] for e in entries]
    assert "transfer_cancelled" in events
    assert "tool_complete" not in events
