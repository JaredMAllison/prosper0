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
