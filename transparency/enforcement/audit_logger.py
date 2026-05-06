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
