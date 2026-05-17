import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    email: EmailStr = Field(..., description="Email del usuario para autenticación")
    password: str = Field(..., min_length=1, description="Contraseña en texto plano")


class UsuarioPublico(BaseModel):
    id: uuid.UUID = Field(..., description="Identificador único del usuario")
    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo")
    rol: str = Field(..., description="Rol de acceso: admin | operador | lectura")


class LoginResponse(BaseModel):
    token: str = Field(..., description="JWT firmado")
    user: UsuarioPublico


class RefreshResponse(BaseModel):
    token: str = Field(..., description="Nuevo JWT tras refresh exitoso")
