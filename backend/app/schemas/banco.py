import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BancoCreate(BaseModel):
    model_config = ConfigDict(strict=True)
    nombre: str = Field(..., min_length=1, max_length=150, description="Nombre del banco")


class BancoUpdate(BaseModel):
    model_config = ConfigDict(strict=True)
    nombre: str = Field(..., min_length=1, max_length=150, description="Nuevo nombre del banco")


class BancoResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Identificador único del banco")
    nombre: str = Field(..., description="Nombre del banco")
    is_active: bool = Field(..., description="Estado activo del banco")
    created_at: datetime = Field(..., description="Fecha de creación del registro")

    model_config = ConfigDict(from_attributes=True)
