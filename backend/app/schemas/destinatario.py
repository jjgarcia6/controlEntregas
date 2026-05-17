import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DestinatarioCreate(BaseModel):
    model_config = ConfigDict(strict=True)
    identificacion: str = Field(..., description="Cédula (10 dígitos) o RUC (13 dígitos) válido módulo 11")
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre completo o razón social")
    direccion: str = Field(..., min_length=1, description="Dirección del destinatario")
    telefono: str = Field(..., min_length=1, max_length=20, description="Teléfono de contacto")
    email: Optional[EmailStr] = Field(None, description="Email de contacto opcional")


class DestinatarioUpdate(BaseModel):
    model_config = ConfigDict(strict=True)
    nombre: Optional[str] = Field(None, max_length=255, description="Nuevo nombre")
    direccion: Optional[str] = Field(None, description="Nueva dirección")
    telefono: Optional[str] = Field(None, max_length=20, description="Nuevo teléfono")
    email: Optional[EmailStr] = Field(None, description="Nuevo email de contacto")


class DestinatarioResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Identificador único del destinatario")
    tipo_identificacion: Literal["cedula", "ruc"] = Field(..., description="Tipo detectado automáticamente: cedula | ruc")
    identificacion: str = Field(..., description="Cédula (10 dígitos) o RUC (13 dígitos)")
    nombre: str = Field(..., description="Nombre completo o razón social")
    direccion: str = Field(..., description="Dirección del destinatario")
    telefono: str = Field(..., description="Teléfono de contacto")
    email: Optional[str] = Field(None, description="Email de contacto opcional")
    is_active: bool = Field(..., description="Estado activo del destinatario")
    created_at: datetime = Field(..., description="Fecha de creación del registro")

    model_config = ConfigDict(from_attributes=True)
