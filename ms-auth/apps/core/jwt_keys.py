"""Claves RSA para JWT asimetrico y documento JWKS."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from django.conf import settings

KEYS_DIR = Path(settings.BASE_DIR) / "keys"
PRIVATE_KEY_FILE = KEYS_DIR / "jwt_private.pem"
PUBLIC_KEY_FILE = KEYS_DIR / "jwt_public.pem"
JWK_KID = "agm-auth-1"


def ensure_rsa_keypair() -> None:
    """Genera par RSA si no existe (desarrollo / primer arranque)."""
    if PRIVATE_KEY_FILE.is_file() and PUBLIC_KEY_FILE.is_file():
        return

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    PRIVATE_KEY_FILE.write_bytes(private_pem)
    PUBLIC_KEY_FILE.write_bytes(public_pem)


def get_rsa_private_key_pem() -> str:
    ensure_rsa_keypair()
    return PRIVATE_KEY_FILE.read_text(encoding="utf-8")


def get_rsa_public_key_pem() -> str:
    ensure_rsa_keypair()
    return PUBLIC_KEY_FILE.read_text(encoding="utf-8")


def build_jwks_document() -> dict:
    """Documento JWKS para validacion local en MS-2..MS-7."""
    from cryptography.hazmat.primitives import serialization

    ensure_rsa_keypair()
    public_key = serialization.load_pem_public_key(PUBLIC_KEY_FILE.read_bytes())
    numbers = public_key.public_numbers()

    def _int_to_base64url(value: int) -> str:
        length = (value.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(value.to_bytes(length, "big")).decode("ascii").rstrip("=")

    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": JWK_KID,
                "n": _int_to_base64url(numbers.n),
                "e": _int_to_base64url(numbers.e),
            }
        ]
    }


def get_jwks_json() -> str:
    return json.dumps(build_jwks_document(), separators=(",", ":"))
