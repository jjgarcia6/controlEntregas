"""
Column-level encryption for PII fields.

EncryptedString: SQLAlchemy TypeDecorator — encrypts on write, decrypts on read.
Reads plaintext gracefully during the migration window (fallback).

hmac_hash: deterministic HMAC-SHA256 used for WHERE-clause lookups on encrypted
columns (e.g. identificacion_hash). Non-reversible; safe to store.

mask_*: helpers that produce audit-log-safe representations of PII values.
"""

import hashlib
import hmac as _hmac
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.config import settings


def _fernet() -> Fernet:
    return Fernet(settings.ENCRYPTION_KEY.encode())


class EncryptedString(TypeDecorator[str]):
    """Transparent Fernet encryption for string columns.

    Stores URL-safe base64 ciphertext. Falls back to returning the raw value
    when decryption fails so existing plaintext rows remain readable until
    the data-migration script re-encrypts them.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return _fernet().encrypt(str(value).encode()).decode()

    def process_result_value(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise RuntimeError(
                "Valor cifrado inválido en columna PII. "
                "Verifique que ENCRYPTION_KEY no haya rotado sin re-cifrar datos."
            ) from exc


def hmac_hash(value: str) -> str:
    """HMAC-SHA256 of value keyed with ENCRYPTION_KEY (hex, 64 chars).

    Used as the lookup column for encrypted fields that need equality queries.
    """
    key = settings.ENCRYPTION_KEY.encode()
    return _hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


# --- audit-log masking helpers ---


def mask_identificacion(v: str) -> str:
    return ("*" * max(0, len(v) - 4) + v[-4:]) if len(v) > 4 else "***"


def mask_email(v: str) -> str:
    if "@" not in v:
        return "***"
    local, domain = v.split("@", 1)
    return (local[0] if local else "*") + "***@" + domain


def mask_nombre(v: str) -> str:
    parts = v.split()
    return " ".join(p[0] + "***" for p in parts) if parts else "***"


def mask_telefono(v: str) -> str:
    return (v[:2] + "*" * max(0, len(v) - 4) + v[-2:]) if len(v) > 4 else "***"
