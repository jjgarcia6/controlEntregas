import json
from typing import Any, List

from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors(v: Any) -> List[str]:
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    return []


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    DATABASE_URL: str
    JWT_SECRET_KEY: str
    # 32-byte URL-safe base64 Fernet key. Generate with:
    # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # REQUERIDA. Sin default. DEBE proveerse vía env-var o GCP Secret Manager.
    ENCRYPTION_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    JWT_REFRESH_LEEWAY_SECONDS: int = 900
    CORS_ORIGINS: str = '["http://localhost:5173"]'
    ENVIRONMENT: str = "production"
    ADMIN_EMAIL: str = "admin@sistema.com"
    ADMIN_PASSWORD: str
    MAX_XML_UPLOAD_MB: int = 1

    @property
    def cors_origins_list(self) -> List[str]:
        return _parse_cors(self.CORS_ORIGINS)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def clean_database_url(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def coerce_to_str(cls, v: Any) -> Any:
        if isinstance(v, list):
            return json.dumps(v)
        return v

    @field_validator("ENCRYPTION_KEY", mode="after")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        placeholder = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        if v == placeholder:
            raise ValueError(
                "ENCRYPTION_KEY usa el valor placeholder de desarrollo. "
                "Genere una clave nueva con Fernet.generate_key()."
            )
        try:
            Fernet(v.encode())
        except ValueError as exc:
            raise ValueError(
                f"ENCRYPTION_KEY no es una Fernet key válida: {exc}"
            ) from exc
        return v

    @field_validator("MAX_XML_UPLOAD_MB", mode="after")
    @classmethod
    def validate_xml_size(cls, v: int) -> int:
        if v < 1 or v > 50:
            raise ValueError("MAX_XML_UPLOAD_MB debe estar entre 1 y 50")
        return v

    MAX_REQUEST_BODY_MB: int = 2

    @field_validator("MAX_REQUEST_BODY_MB", mode="after")
    @classmethod
    def validate_request_body_size(cls, v: int) -> int:
        if v < 1 or v > 50:
            raise ValueError("MAX_REQUEST_BODY_MB debe estar entre 1 y 50")
        return v

    @field_validator("JWT_SECRET_KEY", mode="after")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        if not isinstance(v, str) or len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY debe tener al menos 32 caracteres. "
                "Genere una clave segura con: "
                "python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )
        return v

    @field_validator("JWT_REFRESH_LEEWAY_SECONDS", mode="after")
    @classmethod
    def validate_refresh_leeway(cls, v: int) -> int:
        if v < 60 or v > 3600:
            raise ValueError(
                "JWT_REFRESH_LEEWAY_SECONDS debe estar entre 60 (1 min) y 3600 (1 hora). "
                "Valores mayores aumentan la ventana de uso de tokens robados."
            )
        return v


settings: Settings = Settings()  # type: ignore[call-arg]
