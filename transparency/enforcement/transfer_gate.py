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
