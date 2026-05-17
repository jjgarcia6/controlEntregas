import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(strict=True)
    email: EmailStr = Field(..., description="Email único del usuario")
    password: str = Field(..., min_length=8, description="Contraseña inicial")
    nombre: str = Field(..., min_length=1, max_length=150, description="Nombre completo")
    rol: Literal["admin", "operador", "lectura"] = Field(..., description="Rol de acceso")


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(strict=True)
    email: Optional[EmailStr] = Field(None, description="Nuevo email")
    nombre: Optional[str] = Field(None, min_length=1, max_length=150, description="Nuevo nombre")
    rol: Optional[Literal["admin", "operador", "lectura"]] = Field(None, description="Nuevo rol")


class PasswordUpdate(BaseModel):
    model_config = ConfigDict(strict=True)
    nueva_password: str = Field(..., min_length=8, description="Nueva contraseña para reset")


class UsuarioResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Identificador único del usuario")
    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo")
    rol: str = Field(..., description="Rol de acceso: admin | operador | lectura")
    ultimo_login: Optional[datetime] = Field(None, description="Fecha y hora del último acceso")
    is_active: bool = Field(..., description="Estado activo del usuario")
    created_at: datetime = Field(..., description="Fecha de creación del registro")

    model_config = ConfigDict(from_attributes=True)
