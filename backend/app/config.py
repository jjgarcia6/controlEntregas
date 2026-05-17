from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    ENVIRONMENT: str = "development"
    ADMIN_EMAIL: str = "admin@sistema.com"
    ADMIN_PASSWORD: str


settings: Settings = Settings()  # type: ignore[call-arg]
