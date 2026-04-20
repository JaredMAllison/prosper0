# Enforcement Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stack-agnostic middleware chain that enforces tool authorization, self-certification for data transfers, and an append-only audit log with content hashing.

**Architecture:** Four independent components (ConfigVerifier, ToolGate, TransferGate, AuditLogger) assembled into an EnforcementChain. Every tool call passes through the chain in sequence. Fail-closed throughout — if any component can't do its job, the system exits.

**Tech Stack:** Python 3.11+, `pyyaml`, `cryptography` (Ed25519 signatures), `pytest`, stdlib `smtplib` / `hashlib` / `json`

---

## File Map

**Create:**
```
pyproject.toml
transparency/__init__.py
transparency/enforcement/__init__.py
transparency/enforcement/config.py         ← dataclasses: ToolRule, TransferConfig, ToolsConfig
transparency/enforcement/audit_logger.py   ← AuditLogger: append-only JSON log, content hashing
transparency/enforcement/tool_gate.py      ← ToolGate: per-call authorization against config
transparency/enforcement/config_verifier.py ← ConfigVerifier: Ed25519 signature check at startup
transparency/enforcement/transfer_gate.py  ← TransferGate: self-certification flow, SMTP send
transparency/enforcement/chain.py          ← EnforcementChain: assembles and runs the chain
transparency/enforcement/signing.py        ← CLI helper: generate key pair + sign config
tests/__init__.py
tests/tool_config/__init__.py
tests/tool_config/conftest.py              ← shared fixtures: tmp config, key pairs, sample vault
tests/tool_config/test_audit_logger.py
tests/tool_config/test_tool_gate.py
tests/tool_config/test_config_verifier.py
tests/tool_config/test_transfer_gate.py
tests/tool_config/test_chain.py
```

**Do not modify:**
- Any existing README.md files
- `stack/tools.config.yaml` (placeholder — the real one is operator-written)

---

## Task 0: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `transparency/__init__.py`
- Create: `transparency/enforcement/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/tool_config/__init__.py`

- [ ] **Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "prosper0"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "cryptography>=41.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-mock>=3.12",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty package init files**

```bash
touch transparency/__init__.py
touch transparency/enforcement/__init__.py
touch tests/__init__.py
touch tests/tool_config/__init__.py
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -e ".[dev]"
```

Expected: installs pyyaml, cryptography, pytest, pytest-mock with no errors.

- [ ] **Step 4: Verify pytest runs**

```bash
pytest tests/ -v
```

Expected: `no tests ran` — not a failure.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml transparency/__init__.py transparency/enforcement/__init__.py tests/__init__.py tests/tool_config/__init__.py
git commit -m "chore: python project setup with enforcement package skeleton"
```

---

## Task 1: Config Dataclasses

**Files:**
- Create: `transparency/enforcement/config.py`
- Create: `tests/tool_config/conftest.py`

- [ ] **Step 1: Write the failing test**

Create `tests/tool_config/conftest.py`:

```python
import pytest
import yaml
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption
)

SAMPLE_CONFIG = {
    "version": 1,
    "signed_by": "employer@company.com",
    "tools": {
        "allowed": [
            {"name": "read_vault_file", "paths": ["prosper0-vault/**"]},
            {"name": "write_vault_file", "paths": ["prosper0-vault/Tasks/**", "prosper0-vault/Inbox.md"]},
            {"name": "search_vault"},
        ],
        "denied": [
            {"name": "read_vault_file", "paths": ["prosper0-vault/Contacts/**"]},
        ],
    },
    "transfer": {
        "allowed": True,
        "max_size_kb": 50,
        "employer_email": "employer@company.com",
    },
}

@pytest.fixture
def sample_config_dict():
    return SAMPLE_CONFIG

@pytest.fixture
def key_pair(tmp_path):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_pem = tmp_path / "employer.private.pem"
    public_pem = tmp_path / "employer.public.pem"
    private_pem.write_bytes(
        private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    )
    public_pem.write_bytes(
        public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    )
    return private_key, public_key, private_pem, public_pem

@pytest.fixture
def signed_config(tmp_path, key_pair):
    private_key, _, _, public_pem = key_pair
    config_path = tmp_path / "tools.config.yaml"
    config_bytes = yaml.dump(SAMPLE_CONFIG).encode()
    config_path.write_bytes(config_bytes)
    sig_path = tmp_path / "tools.config.yaml.sig"
    sig_path.write_bytes(private_key.sign(config_bytes))
    return config_path, sig_path, public_pem
```

Create `tests/tool_config/test_audit_logger.py` (will be filled in Task 2 — create empty for now):

```python
# filled in Task 2
```

Now write the first real test in a temporary file to verify config parsing:

Create `tests/tool_config/test_config.py`:

```python
from transparency.enforcement.config import ToolsConfig, ToolRule, TransferConfig

def test_toolsconfig_from_dict(sample_config_dict):
    config = ToolsConfig.from_dict(sample_config_dict)
    assert config.version == 1
    assert config.signed_by == "employer@company.com"
    assert len(config.allowed_tools) == 3
    assert len(config.denied_tools) == 1
    assert config.allowed_tools[0].name == "read_vault_file"
    assert "prosper0-vault/**" in config.allowed_tools[0].paths
    assert config.transfer.allowed is True
    assert config.transfer.employer_email == "employer@company.com"

def test_tool_rule_no_paths():
    rule = ToolRule(name="search_vault", paths=[])
    assert rule.paths == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tool_config/test_config.py -v
```

Expected: `ImportError: cannot import name 'ToolsConfig'`

- [ ] **Step 3: Write minimal implementation**

Create `transparency/enforcement/config.py`:

```python
from dataclasses import dataclass, field


@dataclass
class ToolRule:
    name: str
    paths: list[str] = field(default_factory=list)


@dataclass
class TransferConfig:
    allowed: bool
    max_size_kb: int
    employer_email: str


@dataclass
class ToolsConfig:
    version: int
    signed_by: str
    allowed_tools: list[ToolRule]
    denied_tools: list[ToolRule]
    transfer: TransferConfig

    @classmethod
    def from_dict(cls, data: dict) -> "ToolsConfig":
        tools = data.get("tools", {})
        allowed = [
            ToolRule(name=t["name"], paths=t.get("paths", []))
            for t in tools.get("allowed", [])
        ]
        denied = [
            ToolRule(name=t["name"], paths=t.get("paths", []))
            for t in tools.get("denied", [])
        ]
        t = data["transfer"]
        transfer = TransferConfig(
            allowed=t["allowed"],
            max_size_kb=t["max_size_kb"],
            employer_email=t["employer_email"],
        )
        return cls(
            version=data["version"],
            signed_by=data["signed_by"],
            allowed_tools=allowed,
            denied_tools=denied,
            transfer=transfer,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tool_config/test_config.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transparency/enforcement/config.py tests/tool_config/conftest.py tests/tool_config/test_config.py
git commit -m "feat: add ToolsConfig dataclasses with from_dict parser"
```

---

## Task 2: AuditLogger

**Files:**
- Create: `transparency/enforcement/audit_logger.py`
- Modify: `tests/tool_config/test_audit_logger.py`

- [ ] **Step 1: Write the failing tests**

Overwrite `tests/tool_config/test_audit_logger.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tool_config/test_audit_logger.py -v
```

Expected: `ImportError: cannot import name 'AuditLogger'`

- [ ] **Step 3: Write minimal implementation**

Create `transparency/enforcement/audit_logger.py`:

```python
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class AuditLogger:
    def __init__(self, log_dir: Path) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _log_file(self) -> Path:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"audit-{date}.log"

    def _append(self, entry: dict) -> None:
        with open(self._log_file(), "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log_attempt(self, tool: str, path: Optional[str], session_id: str) -> None:
        self._append({"timestamp": self._ts(), "event": "tool_attempt",
                       "tool": tool, "path": path, "session_id": session_id})

    def log_complete(self, tool: str, path: Optional[str], session_id: str, content: bytes) -> None:
        self._append({
            "timestamp": self._ts(), "event": "tool_complete", "tool": tool, "path": path,
            "outcome": "success",
            "content_hash": f"sha256:{hashlib.sha256(content).hexdigest()}",
            "bytes": len(content), "session_id": session_id,
        })

    def log_rejected(self, tool: str, path: Optional[str], session_id: str, reason: str) -> None:
        self._append({"timestamp": self._ts(), "event": "tool_rejected",
                       "tool": tool, "path": path, "reason": reason, "session_id": session_id})

    def log_transfer_cancelled(self, content_hash: str, session_id: str) -> None:
        self._append({"timestamp": self._ts(), "event": "transfer_cancelled",
                       "content_hash": content_hash, "operator_confirmed": False,
                       "session_id": session_id})

    def log_transfer_complete(self, content_hash: str, email_message_id: str,
                               reason: str, session_id: str) -> None:
        self._append({
            "timestamp": self._ts(), "event": "transfer_complete",
            "content_hash": content_hash, "email_message_id": email_message_id,
            "reason": reason, "operator_confirmed": True, "session_id": session_id,
        })
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tool_config/test_audit_logger.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transparency/enforcement/audit_logger.py tests/tool_config/test_audit_logger.py
git commit -m "feat: add AuditLogger with append-only JSON log and content hashing"
```

---

## Task 3: ToolGate

**Files:**
- Create: `transparency/enforcement/tool_gate.py`
- Create: `tests/tool_config/test_tool_gate.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tool_config/test_tool_gate.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tool_config/test_tool_gate.py -v
```

Expected: `ImportError: cannot import name 'ToolGate'`

- [ ] **Step 3: Write minimal implementation**

Create `transparency/enforcement/tool_gate.py`:

```python
import fnmatch
from typing import Optional
from transparency.enforcement.config import ToolsConfig


class ToolNotAuthorizedError(Exception):
    pass


class ToolGate:
    def __init__(self, config: ToolsConfig) -> None:
        self._config = config

    def check(self, tool_name: str, path: Optional[str] = None) -> None:
        """Raise ToolNotAuthorizedError if the call is not permitted."""
        # Explicit deny wins over allow
        for rule in self._config.denied_tools:
            if rule.name == tool_name:
                if not rule.paths or self._matches_any(path, rule.paths):
                    raise ToolNotAuthorizedError(
                        f"Tool '{tool_name}' is not authorized for path '{path}'."
                    )

        # Must appear in allow list
        for rule in self._config.allowed_tools:
            if rule.name == tool_name:
                if not rule.paths or self._matches_any(path, rule.paths):
                    return

        raise ToolNotAuthorizedError(
            f"Tool '{tool_name}' is not authorized for path '{path}'."
        )

    def _matches_any(self, path: Optional[str], patterns: list[str]) -> bool:
        if path is None:
            return True
        return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tool_config/test_tool_gate.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transparency/enforcement/tool_gate.py tests/tool_config/test_tool_gate.py
git commit -m "feat: add ToolGate with deny-first path authorization"
```

---

## Task 4: ConfigVerifier

**Files:**
- Create: `transparency/enforcement/config_verifier.py`
- Create: `transparency/enforcement/signing.py`
- Create: `tests/tool_config/test_config_verifier.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tool_config/test_config_verifier.py`:

```python
import pytest
import yaml
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption
)
from transparency.enforcement.config_verifier import ConfigVerifier, ConfigVerificationError
from transparency.enforcement.config import ToolsConfig


def test_valid_config_loads(signed_config):
    config_path, sig_path, public_pem = signed_config
    verifier = ConfigVerifier(config_path, sig_path, public_pem)
    config = verifier.load_and_verify()
    assert isinstance(config, ToolsConfig)
    assert config.version == 1
    assert config.signed_by == "employer@company.com"


def test_missing_config_raises(signed_config):
    config_path, sig_path, public_pem = signed_config
    config_path.unlink()
    verifier = ConfigVerifier(config_path, sig_path, public_pem)
    with pytest.raises(ConfigVerificationError, match="Config file not found"):
        verifier.load_and_verify()


def test_missing_sig_raises(signed_config):
    config_path, sig_path, public_pem = signed_config
    sig_path.unlink()
    verifier = ConfigVerifier(config_path, sig_path, public_pem)
    with pytest.raises(ConfigVerificationError, match="Signature file not found"):
        verifier.load_and_verify()


def test_tampered_config_raises(signed_config, tmp_path):
    config_path, sig_path, public_pem = signed_config
    # Tamper with the config after signing
    config_path.write_text(config_path.read_text() + "\n# tampered\n")
    verifier = ConfigVerifier(config_path, sig_path, public_pem)
    with pytest.raises(ConfigVerificationError, match="invalid"):
        verifier.load_and_verify()


def test_wrong_key_raises(signed_config, tmp_path):
    config_path, sig_path, _ = signed_config
    # Generate a different key pair — public key won't match signature
    wrong_key = Ed25519PrivateKey.generate()
    wrong_public_pem = tmp_path / "wrong.public.pem"
    wrong_public_pem.write_bytes(
        wrong_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    )
    verifier = ConfigVerifier(config_path, sig_path, wrong_public_pem)
    with pytest.raises(ConfigVerificationError, match="invalid"):
        verifier.load_and_verify()


def test_malformed_yaml_raises(signed_config, key_pair, tmp_path):
    private_key, _, _, public_pem = key_pair
    bad_config = tmp_path / "bad.yaml"
    bad_bytes = b"version: [not: valid: yaml"
    bad_config.write_bytes(bad_bytes)
    bad_sig = tmp_path / "bad.yaml.sig"
    bad_sig.write_bytes(private_key.sign(bad_bytes))
    verifier = ConfigVerifier(bad_config, bad_sig, public_pem)
    with pytest.raises(ConfigVerificationError, match="parse error"):
        verifier.load_and_verify()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tool_config/test_config_verifier.py -v
```

Expected: `ImportError: cannot import name 'ConfigVerifier'`

- [ ] **Step 3: Write minimal implementation**

Create `transparency/enforcement/config_verifier.py`:

```python
from pathlib import Path
import yaml
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature
from transparency.enforcement.config import ToolsConfig


class ConfigVerificationError(Exception):
    pass


class ConfigVerifier:
    def __init__(self, config_path: Path, sig_path: Path, public_key_path: Path) -> None:
        self.config_path = Path(config_path)
        self.sig_path = Path(sig_path)
        self.public_key_path = Path(public_key_path)

    def load_and_verify(self) -> ToolsConfig:
        """Load and verify the signed config. Raises ConfigVerificationError on any failure."""
        if not self.config_path.exists():
            raise ConfigVerificationError(f"Config file not found: {self.config_path}")
        if not self.sig_path.exists():
            raise ConfigVerificationError(f"Signature file not found: {self.sig_path}")
        if not self.public_key_path.exists():
            raise ConfigVerificationError(f"Public key not found: {self.public_key_path}")

        config_bytes = self.config_path.read_bytes()
        sig_bytes = self.sig_path.read_bytes()

        try:
            public_key = load_pem_public_key(self.public_key_path.read_bytes())
            public_key.verify(sig_bytes, config_bytes)
        except InvalidSignature:
            raise ConfigVerificationError(
                "Config signature is invalid — file may have been tampered with."
            )
        except Exception as e:
            raise ConfigVerificationError(f"Signature verification failed: {e}")

        try:
            data = yaml.safe_load(config_bytes)
        except yaml.YAMLError as e:
            raise ConfigVerificationError(f"Config parse error: {e}")

        return ToolsConfig.from_dict(data)
```

Create `transparency/enforcement/signing.py` (operator/employer CLI tool):

```python
"""
CLI helper for employers to generate key pairs and sign tools.config.yaml.

Usage:
  python -m transparency.enforcement.signing generate --out-dir ./keys
  python -m transparency.enforcement.signing sign tools.config.yaml --key ./keys/employer.private.pem
"""
import sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key, Encoding, PublicFormat, PrivateFormat, NoEncryption
)


def generate(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    private_pem = out_dir / "employer.private.pem"
    public_pem = out_dir / "employer.public.pem"
    private_pem.write_bytes(
        private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    )
    public_pem.write_bytes(
        private_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    )
    print(f"Key pair written to {out_dir}/")
    print(f"  Private (keep secret): {private_pem}")
    print(f"  Public (goes on drive): {public_pem}")


def sign(config_path: Path, private_key_path: Path) -> None:
    config_bytes = config_path.read_bytes()
    private_key = load_pem_private_key(private_key_path.read_bytes(), password=None)
    sig = private_key.sign(config_bytes)
    sig_path = config_path.with_suffix(config_path.suffix + ".sig")
    sig_path.write_bytes(sig)
    print(f"Signed: {sig_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    gen_parser = subparsers.add_parser("generate")
    gen_parser.add_argument("--out-dir", type=Path, default=Path("./keys"))
    sign_parser = subparsers.add_parser("sign")
    sign_parser.add_argument("config", type=Path)
    sign_parser.add_argument("--key", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.out_dir)
    elif args.command == "sign":
        sign(args.config, args.key)
    else:
        parser.print_help()
        sys.exit(1)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tool_config/test_config_verifier.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transparency/enforcement/config_verifier.py transparency/enforcement/signing.py tests/tool_config/test_config_verifier.py
git commit -m "feat: add ConfigVerifier with Ed25519 signature enforcement and signing CLI"
```

---

## Task 5: TransferGate

**Files:**
- Create: `transparency/enforcement/transfer_gate.py`
- Create: `tests/tool_config/test_transfer_gate.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tool_config/test_transfer_gate.py`:

```python
import hashlib
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
    import json
    from pathlib import Path
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
    # If we get here without StopIteration, the gate reprompted correctly


def test_confirmed_transfer_sends_email_and_logs(gate, audit, tmp_path):
    content = b"project status update"
    expected_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
    mock_send = MagicMock(return_value="<test-msg-id@smtp>")
    with patch("builtins.input", side_effect=["sharing status update with manager for review", "yes"]):
        with patch.object(gate, "_send_email", mock_send):
            gate.certify(content, "project status")
    mock_send.assert_called_once()
    import json
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tool_config/test_transfer_gate.py -v
```

Expected: `ImportError: cannot import name 'TransferGate'`

- [ ] **Step 3: Write minimal implementation**

Create `transparency/enforcement/transfer_gate.py`:

```python
import hashlib
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional
from transparency.enforcement.audit_logger import AuditLogger
from transparency.enforcement.config import ToolsConfig


class TransferCancelledError(Exception):
    pass


class TransferGate:
    MIN_REASON_LENGTH = 20

    def __init__(self, config: ToolsConfig, audit: AuditLogger,
                 smtp_config: dict, session_id: str) -> None:
        self._config = config
        self._audit = audit
        self._smtp = smtp_config
        self._session_id = session_id

    def certify(self, content: bytes, content_description: str) -> str:
        """Run self-certification. Returns email message ID. Raises TransferCancelledError."""
        if not self._config.transfer.allowed:
            raise TransferCancelledError("Data transfer is not permitted by the current config.")

        content_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"

        print(f"\n{'='*60}")
        print(f"TRANSFER REQUEST")
        print(f"Description: {content_description}")
        print(f"Size: {len(content)} bytes  |  Hash: {content_hash}")
        print(f"\n--- Full Content ---")
        print(content.decode(errors="replace"))
        print(f"{'='*60}\n")

        reason = self._get_reason()
        msg = self._draft_email(content, content_hash, reason)

        print(f"\n--- Email Preview ---")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        print(f"\n{msg.get_body().get_content()}")
        print(f"---------------------\n")

        confirm = input("Send this email and execute transfer? [yes/no]: ").strip().lower()
        if confirm != "yes":
            self._audit.log_transfer_cancelled(content_hash, self._session_id)
            raise TransferCancelledError("Transfer cancelled by operator.")

        message_id = self._send_email(msg)
        self._audit.log_transfer_complete(content_hash, message_id, reason, self._session_id)
        return message_id

    def _get_reason(self) -> str:
        while True:
            reason = input("Reason for transfer (min 20 chars): ").strip()
            if len(reason) >= self.MIN_REASON_LENGTH:
                return reason
            print(f"Reason too short ({len(reason)} chars). Be specific.")

    def _draft_email(self, content: bytes, content_hash: str, reason: str) -> EmailMessage:
        msg = EmailMessage()
        msg["To"] = self._config.transfer.employer_email
        msg["From"] = self._smtp.get("from_addr", "prosper0@local")
        short_reason = reason[:60]
        msg["Subject"] = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} Data Transfer — {short_reason}"
        body = (
            f"Reason: {reason}\n\n"
            f"Content:\n{content.decode(errors='replace')}\n\n"
            f"Content hash: {content_hash}\n"
            f"Session: {self._session_id}\n"
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
        )
        msg.set_content(body)
        return msg

    def _send_email(self, msg: EmailMessage) -> str:
        with smtplib.SMTP(self._smtp.get("host", "localhost"),
                          self._smtp.get("port", 25)) as server:
            server.send_message(msg)
        return msg.get("Message-ID", "<no-id>")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tool_config/test_transfer_gate.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transparency/enforcement/transfer_gate.py tests/tool_config/test_transfer_gate.py
git commit -m "feat: add TransferGate with self-certification flow and SMTP send"
```

---

## Task 6: EnforcementChain

**Files:**
- Create: `transparency/enforcement/chain.py`
- Update: `transparency/enforcement/__init__.py`
- Create: `tests/tool_config/test_chain.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tool_config/test_chain.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tool_config/test_chain.py -v
```

Expected: `ImportError: cannot import name 'EnforcementChain'`

- [ ] **Step 3: Write minimal implementation**

Create `transparency/enforcement/chain.py`:

```python
from pathlib import Path
from typing import Callable, Optional
from transparency.enforcement.audit_logger import AuditLogger
from transparency.enforcement.config import ToolsConfig
from transparency.enforcement.tool_gate import ToolGate, ToolNotAuthorizedError
from transparency.enforcement.transfer_gate import TransferGate


class EnforcementChain:
    def __init__(self, config: ToolsConfig, audit: AuditLogger,
                 smtp_config: dict, session_id: str, log_dir: Path) -> None:
        self._config = config
        self._audit = audit
        self._session_id = session_id
        self._tool_gate = ToolGate(config)
        self._transfer_gate = TransferGate(
            config=config, audit=audit,
            smtp_config=smtp_config, session_id=session_id,
        )

    def call(self, tool_name: str, path: Optional[str],
             executor: Callable[[], bytes], is_transfer: bool = False) -> bytes:
        """Run the full enforcement chain for one tool call."""
        self._audit.log_attempt(tool_name, path, self._session_id)

        try:
            self._tool_gate.check(tool_name, path)
        except ToolNotAuthorizedError:
            self._audit.log_rejected(tool_name, path, self._session_id, "path_not_authorized")
            raise

        content = executor()

        if is_transfer:
            self._transfer_gate.certify(content, f"{tool_name}: {path}")

        self._audit.log_complete(tool_name, path, self._session_id, content)
        return content
```

Update `transparency/enforcement/__init__.py`:

```python
from transparency.enforcement.chain import EnforcementChain
from transparency.enforcement.config_verifier import ConfigVerifier, ConfigVerificationError
from transparency.enforcement.tool_gate import ToolNotAuthorizedError
from transparency.enforcement.transfer_gate import TransferCancelledError

__all__ = [
    "EnforcementChain",
    "ConfigVerifier",
    "ConfigVerificationError",
    "ToolNotAuthorizedError",
    "TransferCancelledError",
]
```

- [ ] **Step 4: Run the full test suite**

```bash
pytest tests/tool_config/ -v
```

Expected: all tests PASS. Count should be 25+.

- [ ] **Step 5: Commit**

```bash
git add transparency/enforcement/chain.py transparency/enforcement/__init__.py tests/tool_config/test_chain.py
git commit -m "feat: add EnforcementChain assembling all middleware components"
```

---

## Task 7: Integration Test

**Files:**
- Create: `tests/tool_config/test_integration.py`

- [ ] **Step 1: Write the integration test**

Create `tests/tool_config/test_integration.py`:

```python
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


def test_full_chain_authorized_read(signed_config, tmp_path):
    config_path, sig_path, public_pem = signed_config
    verifier = ConfigVerifier(config_path, sig_path, public_pem)
    config = verifier.load_and_verify()

    from transparency.enforcement.audit_logger import AuditLogger
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

    from transparency.enforcement.audit_logger import AuditLogger
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
```

- [ ] **Step 2: Run integration test**

```bash
pytest tests/tool_config/test_integration.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 3: Run full suite one final time**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests PASS. Zero failures.

- [ ] **Step 4: Final commit**

```bash
git add tests/tool_config/test_integration.py
git commit -m "test: add integration test for full enforcement chain"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| ConfigVerifier: signature check at startup, exits if invalid | Task 4 |
| Config mounted read-only (Docker) | Documented in spec; enforced at deploy time, not in Python |
| ToolGate: deny-first, per-call, no partial execution | Task 3 |
| ToolGate: error doesn't enumerate allowed paths | Task 3, test_error_message_does_not_enumerate_allowed_paths |
| AuditLogger: pre+post entries, content hash | Task 2 |
| AuditLogger: append-only, daily rotation | Task 2 |
| AuditLogger: gap detection (pre without post) | Structural — pre-entry always written before execution; gap is inherent |
| TransferGate: operator sees full content before confirm | Task 5 |
| TransferGate: typed reason, min length | Task 5 |
| TransferGate: email with full content + hash sent to employer | Task 5 |
| TransferGate: cancelled transfers logged with hash | Task 5 |
| Fail-closed: config invalid → exit | Task 4 (ConfigVerificationError) |
| Fail-closed: AuditLogger can't write → exit | Not tested — add note: orchestrator must catch OSError from AuditLogger and exit |
| Fail-closed: SMTP fails → transfer blocked | Task 5 (exception propagates from _send_email) |
| Full chain integration | Task 7 |

**Gap:** AuditLogger `OSError` on write is not tested. Add to test_audit_logger.py in a follow-up.

**Type consistency:** `ToolsConfig.from_dict` used in Tasks 1, 3, 4, 5, 6 — consistent. `AuditLogger(log_dir=...)` used in Tasks 2, 5, 6, 7 — consistent. `chain.call(tool_name=, path=, executor=, is_transfer=)` defined in Task 6, used in Task 7 — consistent.
