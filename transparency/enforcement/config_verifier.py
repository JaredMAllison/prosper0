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
