import pytest

from app.utils.encryption import EncryptedString
from app.utils.exceptions import ValidacionNegocio
from app.utils.validaciones import validar_identificacion


def test_should_validate_valid_cedula() -> None:
    result = validar_identificacion("1713175071")
    assert result["tipo"] == "cedula"
    assert result["identificacion"] == "1713175071"


def test_should_validate_valid_ruc() -> None:
    result = validar_identificacion("1713175071001")
    assert result["tipo"] == "ruc"
    assert result["identificacion"] == "1713175071001"


def test_should_reject_invalid_digito_verificador() -> None:
    with pytest.raises(ValidacionNegocio, match="Dígito verificador"):
        validar_identificacion("1713175079")


def test_should_reject_wrong_length() -> None:
    with pytest.raises(ValidacionNegocio, match="Longitud inválida"):
        validar_identificacion("12345")


def test_should_reject_non_digit_characters() -> None:
    with pytest.raises(ValidacionNegocio, match="solo dígitos"):
        validar_identificacion("171234AB78")


def test_b2_plaintext_residual_lanza_runtime_error() -> None:
    """B2: plaintext en columna PII debe lanzar RuntimeError, no leerse en claro."""
    es = EncryptedString()
    with pytest.raises(RuntimeError) as exc_info:
        es.process_result_value("texto-plano-sin-cifrar", None)
    assert "PII" in str(exc_info.value)


def test_b2_cifra_y_descifra_roundtrip() -> None:
    """Sanity check: el cifrado normal sigue funcionando."""
    es = EncryptedString()
    ciphertext = es.process_bind_param("dato sensible", None)
    assert ciphertext != "dato sensible"
    plaintext = es.process_result_value(ciphertext, None)
    assert plaintext == "dato sensible"
