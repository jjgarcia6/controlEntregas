import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EntregaItemRequest(BaseModel):
    producto_id: uuid.UUID = Field(..., description="ID del producto a entregar")
    cantidad: Decimal = Field(
        ...,
        gt=0,
        decimal_places=4,
        description="Cantidad a entregar. Debe ser mayor a 0 y no superar el saldo disponible",
    )


class EntregaRequest(BaseModel):
    destinatario_id: uuid.UUID = Field(..., description="ID del destinatario en el catálogo")
    items: list[EntregaItemRequest] = Field(
        ...,
        min_length=1,
        description="Lista de productos a entregar. Al menos uno requerido.",
    )
    comentarios: Optional[str] = Field(
        None,
        max_length=255,
        description="Observaciones libres de la entrega",
    )


class EntregaItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Identificador único del ítem de entrega")
    producto_id: uuid.UUID = Field(..., description="Producto entregado")
    xml_item_id: uuid.UUID = Field(..., description="Ítem de XML de origen del lote consumido")
    codigo_principal: str = Field(..., description="Código del producto")
    descripcion: str = Field(..., description="Descripción del producto")
    cantidad: Decimal = Field(..., description="Unidades entregadas")
    peso_total: Decimal = Field(..., description="Peso total del ítem en kg")
    costo_unitario: Decimal = Field(..., description="Costo FIFO por unidad")
    costo_total: Decimal = Field(..., description="Costo total: cantidad × costo_unitario")


class EntregaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Identificador único de la entrega")
    numero: int = Field(..., description="Número secuencial visible al usuario")
    destinatario_id: uuid.UUID = Field(..., description="ID del destinatario en el catálogo")
    snap_identificacion: str = Field(..., description="Cédula/RUC del destinatario al momento de crear")
    snap_nombre: str = Field(..., description="Nombre del destinatario al momento de crear")
    snap_direccion: str = Field(..., description="Dirección del destinatario al momento de crear")
    snap_telefono: str = Field(..., description="Teléfono del destinatario al momento de crear")
    comentarios: Optional[str] = Field(None, description="Observaciones de la entrega")
    total_entrega: Decimal = Field(..., description="Suma del costo_total de todos los ítems")
    saldo_pendiente: Decimal = Field(..., description="Monto aún no pagado (Fase 5 lo reduce)")
    estado: str = Field(..., description="Estado de la entrega: activa | eliminada")
    items: list[EntregaItemResponse] = Field(default_factory=list, description="Ítems de la entrega")
    created_at: datetime = Field(..., description="Fecha de creación de la entrega")


class EntregaListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Identificador único de la entrega")
    numero: int = Field(..., description="Número secuencial")
    snap_identificacion: str = Field(..., description="Identificación del destinatario (snapshot)")
    snap_nombre: str = Field(..., description="Nombre del destinatario (snapshot)")
    total_entrega: Decimal = Field(..., description="Total de la entrega")
    saldo_pendiente: Decimal = Field(..., description="Saldo sin pagar")
    estado: str = Field(..., description="Estado: activa | eliminada")
    created_at: datetime = Field(..., description="Fecha de creación (ISO 8601)")
