import json
import hashlib
from pathlib import Path
from transparency.enforcement.audit_logger import AuditLogger


def _read_entries(log_dir: Path) -> list[dict]:
    logs = list(log_dir.glob("audit-*.log"))
    assert len(logs) == 1
    return [json.loads(line) for line in logs[0].read_text().strip().splitlines()]


def test_log_attempt(tmp_path):
    logger = AuditLogger(log_dir=tmp_path)
    logger.log_attempt(tool="read_vault_file", path="prosper0-vault/Tasks/task.md", session_id="s1")
    entries = _read_entries(tmp_path)
    assert len(entries) == 1
    assert entries[0]["event"] == "tool_attempt"
    assert entries[0]["tool"] == "read_vault_file"
    assert entries[0]["path"] == "prosper0-vault/Tasks/task.md"
    assert entries[0]["session_id"] == "s1"
    assert "timestamp" in entries[0]


def test_log_complete_includes_hash(tmp_path):
    logger = AuditLogger(log_dir=tmp_path)
    content = b"task content here"
    logger.log_complete(tool="read_vault_file", path="prosper0-vault/Tasks/task.md", session_id="s1", content=content)
    entries = _read_entries(tmp_path)
    expected_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
    assert entries[0]["event"] == "tool_complete"
    assert entries[0]["content_hash"] == expected_hash
    assert entries[0]["bytes"] == len(content)


def test_log_rejected(tmp_path):
    logger = AuditLogger(log_dir=tmp_path)
    logger.log_rejected(tool="read_vault_file", path="prosper0-vault/Contacts/c.md", session_id="s1", reason="path_not_authorized")
    entries = _read_entries(tmp_path)
    assert entries[0]["event"] == "tool_rejected"
    assert entries[0]["reason"] == "path_not_authorized"


def test_log_transfer_cancelled(tmp_path):
    logger = AuditLogger(log_dir=tmp_path)
    logger.log_transfer_cancelled(content_hash="sha256:abc123", session_id="s1")
    entries = _read_entries(tmp_path)
    assert entries[0]["event"] == "transfer_cancelled"
    assert entries[0]["operator_confirmed"] is False


def test_log_transfer_complete(tmp_path):
    logger = AuditLogger(log_dir=tmp_path)
    logger.log_transfer_complete(
        content_hash="sha256:abc123",
        email_message_id="<msg-id@smtp>",
        reason="sharing project status with manager",
        session_id="s1",
    )
    entries = _read_entries(tmp_path)
    assert entries[0]["event"] == "transfer_complete"
    assert entries[0]["operator_confirmed"] is True
    assert entries[0]["email_message_id"] == "<msg-id@smtp>"


def test_multiple_calls_append(tmp_path):
    logger = AuditLogger(log_dir=tmp_path)
    logger.log_attempt(tool="read_vault_file", path="a.md", session_id="s1")
    logger.log_attempt(tool="search_vault", path=None, session_id="s1")
    entries = _read_entries(tmp_path)
    assert len(entries) == 2


def test_log_dir_created_if_missing(tmp_path):
    log_dir = tmp_path / "nested" / "logs"
    logger = AuditLogger(log_dir=log_dir)
    logger.log_attempt(tool="read_vault_file", path=None, session_id="s1")
    assert log_dir.exists()
