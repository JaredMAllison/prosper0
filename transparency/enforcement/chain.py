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
