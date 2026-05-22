"""Tests adicionales para app/utils/encryption.py — B2."""

import pytest

from app.utils.encryption import EncryptedString


def test_b2_valor_none_se_preserva_como_none() -> None:
    """B2: None debe pasar sin cifrar y sin error."""
    es = EncryptedString()
    assert es.process_bind_param(None, None) is None
    assert es.process_result_value(None, None) is None


def test_b2_ciphertext_de_otra_key_lanza_runtime_error() -> None:
    """B2: ciphertext válido pero generado con otra key también debe fallar."""
    from cryptography.fernet import Fernet

    otra_key = Fernet(Fernet.generate_key())
    ciphertext_ajeno = otra_key.encrypt(b"valor").decode()

    es = EncryptedString()
    with pytest.raises(RuntimeError):
        es.process_result_value(ciphertext_ajeno, None)
