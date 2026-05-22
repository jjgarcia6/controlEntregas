"""
Tests para los fixes de seguridad B1-B4: validaciones de Settings + encryption.
Estos tests instancian Settings directamente sin pasar por el conftest, porque
prueban la validación de configuración (que ocurre al arranque).
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config import Settings


def _base_env() -> dict[str, str]:
    """Variables completas válidas para que Settings se instancie sin .env."""
    return {
        "DATABASE_URL": "postgresql+asyncpg://u:p@h:5432/d",
        "JWT_SECRET_KEY": "x" * 48,
        "ENCRYPTION_KEY": "Hpgb6L_OFqJM_Sld79b_lkn4xCK8eL5xGw9CXBV5o5g=",
        "ADMIN_PASSWORD": "AdminPass123!",
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_MINUTES": "60",
        "JWT_REFRESH_LEEWAY_SECONDS": "900",
        "CORS_ORIGINS": '["http://localhost:5173"]',
        "ENVIRONMENT": "production",
        "ADMIN_EMAIL": "admin@sistema.com",
        "MAX_XML_UPLOAD_MB": "1",
        "MAX_REQUEST_BODY_MB": "2",
    }


def test_b3_encryption_key_placeholder_es_rechazada() -> None:
    """B3: la key placeholder de dev no debe permitir arranque."""
    env = _base_env()
    env["ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            Settings()  # type: ignore[call-arg]
        assert "placeholder" in str(exc_info.value).lower()


def test_b3_encryption_key_invalida_es_rechazada() -> None:
    """B3: una key que no es Fernet válida no debe permitir arranque."""
    env = _base_env()
    env["ENCRYPTION_KEY"] = "not-a-valid-fernet-key"
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValidationError):
            Settings()  # type: ignore[call-arg]


def test_b3_encryption_key_valida_permite_arranque() -> None:
    """B3: una Fernet key válida permite instanciar Settings."""
    env = _base_env()
    with patch.dict(os.environ, env, clear=True):
        s = Settings()  # type: ignore[call-arg]
        assert s.ENCRYPTION_KEY == env["ENCRYPTION_KEY"]


def test_b4_environment_se_lee_del_entorno() -> None:
    """B4: ENVIRONMENT es requerido y se lee del entorno; no hay default en código."""
    env = _base_env()
    env["ENVIRONMENT"] = "production"
    with patch.dict(os.environ, env, clear=True):
        s = Settings()  # type: ignore[call-arg]
        assert s.ENVIRONMENT == "production"


def test_m3_jwt_secret_key_corta_es_rechazada() -> None:
    """M3: una JWT_SECRET_KEY de menos de 32 chars no debe permitir arranque."""
    env = _base_env()
    env["JWT_SECRET_KEY"] = "corta"
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            Settings()  # type: ignore[call-arg]
        assert "32 caracteres" in str(exc_info.value)


def test_m3_jwt_secret_key_de_32_chars_es_aceptada() -> None:
    """M3: justo en el mínimo (32 chars) debe ser aceptada."""
    env = _base_env()
    env["JWT_SECRET_KEY"] = "x" * 32
    with patch.dict(os.environ, env, clear=True):
        s = Settings()  # type: ignore[call-arg]
        assert s.JWT_SECRET_KEY == "x" * 32


def test_m4_refresh_leeway_excesivo_es_rechazado() -> None:
    """M4: leeway > 3600s (1h) no debe permitirse."""
    env = _base_env()
    env["JWT_REFRESH_LEEWAY_SECONDS"] = "86400"  # 1 día
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            Settings()  # type: ignore[call-arg]
        assert "JWT_REFRESH_LEEWAY" in str(exc_info.value)


def test_m4_refresh_leeway_900_es_aceptado() -> None:
    """M4: 900s (15 min) es un valor válido dentro del rango permitido (60–3600)."""
    env = _base_env()
    env["JWT_REFRESH_LEEWAY_SECONDS"] = "900"
    with patch.dict(os.environ, env, clear=True):
        s = Settings()  # type: ignore[call-arg]
        assert s.JWT_REFRESH_LEEWAY_SECONDS == 900


def test_m6_max_request_body_mb_fuera_de_rango_es_rechazado() -> None:
    """M6: MAX_REQUEST_BODY_MB debe estar entre 1 y 50."""
    env = _base_env()
    env["MAX_REQUEST_BODY_MB"] = "100"
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValidationError):
            Settings()  # type: ignore[call-arg]
