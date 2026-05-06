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
            {"name": "transfer_data"},
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
