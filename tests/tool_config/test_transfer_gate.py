import hashlib
import json
import pytest
from unittest.mock import MagicMock, patch
from transparency.enforcement.config import ToolsConfig
from transparency.enforcement.audit_logger import AuditLogger
from transparency.enforcement.transfer_gate import TransferGate, TransferCancelledError


@pytest.fixture
def audit(tmp_path):
    return AuditLogger(log_dir=tmp_path / "logs")


@pytest.fixture
def smtp_config():
    return {"host": "localhost", "port": 25, "from_addr": "prosper0@local"}


@pytest.fixture
def gate(sample_config_dict, audit, smtp_config):
    config = ToolsConfig.from_dict(sample_config_dict)
    return TransferGate(config=config, audit=audit, smtp_config=smtp_config, session_id="s1")


def test_cancelled_transfer_is_logged(gate, tmp_path, audit):
    content = b"sensitive project notes"
    with patch("builtins.input", side_effect=["sharing project update with manager", "no"]):
        with pytest.raises(TransferCancelledError):
            gate.certify(content, "project notes")
    logs = list((tmp_path / "logs").glob("audit-*.log"))
    entries = [json.loads(l) for l in logs[0].read_text().strip().splitlines()]
    assert any(e["event"] == "transfer_cancelled" for e in entries)
    cancelled = next(e for e in entries if e["event"] == "transfer_cancelled")
    assert cancelled["operator_confirmed"] is False
    expected_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
    assert cancelled["content_hash"] == expected_hash


def test_reason_too_short_reprompts(gate):
    content = b"some content"
    with patch("builtins.input", side_effect=["too short", "a" * 20, "no"]):
        with pytest.raises(TransferCancelledError):
            gate.certify(content, "some content")


def test_confirmed_transfer_sends_email_and_logs(gate, audit, tmp_path):
    content = b"project status update"
    expected_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
    mock_send = MagicMock(return_value="<test-msg-id@smtp>")
    with patch("builtins.input", side_effect=["sharing status update with manager for review", "yes"]):
        with patch.object(gate, "_send_email", mock_send):
            gate.certify(content, "project status")
    mock_send.assert_called_once()
    logs = list((tmp_path / "logs").glob("audit-*.log"))
    entries = [json.loads(l) for l in logs[0].read_text().strip().splitlines()]
    complete = next(e for e in entries if e["event"] == "transfer_complete")
    assert complete["operator_confirmed"] is True
    assert complete["content_hash"] == expected_hash
    assert complete["email_message_id"] == "<test-msg-id@smtp>"


def test_transfer_not_allowed_raises(sample_config_dict, tmp_path):
    config_dict = {**sample_config_dict, "transfer": {**sample_config_dict["transfer"], "allowed": False}}
    config = ToolsConfig.from_dict(config_dict)
    audit = AuditLogger(log_dir=tmp_path / "logs")
    gate = TransferGate(config=config, audit=audit, smtp_config={}, session_id="s1")
    with pytest.raises(TransferCancelledError, match="not permitted"):
        gate.certify(b"content", "description")
