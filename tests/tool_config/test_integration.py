"""
Full chain integration test: ConfigVerifier → ToolGate → TransferGate → AuditLogger.
Uses real filesystem, real key pairs, real config file.
"""
import json
import hashlib
import pytest
from unittest.mock import patch
from transparency.enforcement import EnforcementChain, ConfigVerifier
from transparency.enforcement.tool_gate import ToolNotAuthorizedError
from transparency.enforcement.audit_logger import AuditLogger


def test_full_chain_authorized_read(signed_config, tmp_path):
    config_path, sig_path, public_pem = signed_config
    verifier = ConfigVerifier(config_path, sig_path, public_pem)
    config = verifier.load_and_verify()

    audit = AuditLogger(log_dir=tmp_path / "logs")
    chain = EnforcementChain(
        config=config, audit=audit,
        smtp_config={"host": "localhost", "port": 25, "from_addr": "test@local"},
        session_id="integration-test",
        log_dir=tmp_path / "logs",
    )

    content = b"task: finish the enforcement layer"
    result = chain.call(
        tool_name="read_vault_file",
        path="prosper0-vault/Tasks/task.md",
        executor=lambda: content,
    )
    assert result == content

    logs = list((tmp_path / "logs").glob("audit-*.log"))
    entries = [json.loads(l) for l in logs[0].read_text().strip().splitlines()]
    assert entries[0]["event"] == "tool_attempt"
    assert entries[1]["event"] == "tool_complete"
    assert entries[1]["content_hash"] == f"sha256:{hashlib.sha256(content).hexdigest()}"


def test_full_chain_blocks_unauthorized(signed_config, tmp_path):
    config_path, sig_path, public_pem = signed_config
    config = ConfigVerifier(config_path, sig_path, public_pem).load_and_verify()

    audit = AuditLogger(log_dir=tmp_path / "logs")
    chain = EnforcementChain(
        config=config, audit=audit,
        smtp_config={}, session_id="integration-test",
        log_dir=tmp_path / "logs",
    )

    with pytest.raises(ToolNotAuthorizedError):
        chain.call(
            tool_name="read_vault_file",
            path="prosper0-vault/Contacts/confidential.md",
            executor=lambda: b"should not run",
        )
