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


def test_tampered_config_raises(signed_config):
    config_path, sig_path, public_pem = signed_config
    config_path.write_text(config_path.read_text() + "\n# tampered\n")
    verifier = ConfigVerifier(config_path, sig_path, public_pem)
    with pytest.raises(ConfigVerificationError, match="invalid"):
        verifier.load_and_verify()


def test_wrong_key_raises(signed_config, tmp_path):
    config_path, sig_path, _ = signed_config
    wrong_key = Ed25519PrivateKey.generate()
    wrong_public_pem = tmp_path / "wrong.public.pem"
    wrong_public_pem.write_bytes(
        wrong_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    )
    verifier = ConfigVerifier(config_path, sig_path, wrong_public_pem)
    with pytest.raises(ConfigVerificationError, match="invalid"):
        verifier.load_and_verify()


def test_malformed_yaml_raises(key_pair, tmp_path):
    private_key, _, _, public_pem = key_pair
    bad_config = tmp_path / "bad.yaml"
    bad_bytes = b"version: [not: valid: yaml"
    bad_config.write_bytes(bad_bytes)
    bad_sig = tmp_path / "bad.yaml.sig"
    bad_sig.write_bytes(private_key.sign(bad_bytes))
    verifier = ConfigVerifier(bad_config, bad_sig, public_pem)
    with pytest.raises(ConfigVerificationError, match="parse error"):
        verifier.load_and_verify()
