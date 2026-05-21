import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.pago import TipoCuenta


class PagoItemRequest(BaseModel):
    entrega_id: uuid.UUID = Field(
        ..., description="ID de la entrega a la que se aplica el monto"
    )
    monto_aplicado: Decimal = Field(
        ...,
        gt=0,
        description="Monto aplicado; no puede superar saldo_pendiente de la entrega",
    )


class PagoRequest(BaseModel):

    numero_comprobante: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Número transcrito del comprobante físico; no es único en el sistema",
    )
    fecha_pago: datetime = Field(
        ..., description="Fecha y hora en que se realizó el pago (ISO 8601)"
    )
    banco_id: uuid.UUID = Field(..., description="ID del banco del catálogo")
    tipo_cuenta: TipoCuenta = Field(..., description="Tipo de instrumento de pago")
    nombre_titular: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Titular de la cuenta o emisor del cheque",
    )
    valor_total: Decimal = Field(
        ...,
        gt=0,
        description="Valor total del comprobante; debe igualar la suma de distribuciones",
    )
    distribuciones: list[PagoItemRequest] = Field(
        ...,
        min_length=1,
        description="Distribución del pago entre entregas activas con saldo",
    )


class PagoItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ID de la línea de distribución")
    entrega_id: uuid.UUID = Field(..., description="ID de la entrega")
    entrega_numero: int = Field(..., description="Número secuencial de la entrega")
    snap_nombre: str = Field(..., description="Nombre del destinatario de la entrega")
    snap_identificacion: str = Field(
        ..., description="Identificación del destinatario de la entrega"
    )
    monto_aplicado: Decimal = Field(..., description="Monto aplicado a esta entrega")


class PagoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Identificador único del pago")
    numero_comprobante: str = Field(..., description="Número del comprobante de pago")
    fecha_pago: datetime = Field(..., description="Fecha y hora del pago")
    banco_id: uuid.UUID = Field(..., description="ID del banco")
    banco_nombre: str = Field(
        ..., description="Nombre del banco (desnormalizado para UI)"
    )
    tipo_cuenta: str = Field(..., description="Tipo de instrumento de pago")
    nombre_titular: str = Field(..., description="Nombre del titular")
    valor_total: Decimal = Field(..., description="Valor total del comprobante")
    valor_aplicado: Decimal = Field(..., description="Suma de montos distribuidos")
    estado: str = Field(..., description="Estado del pago: activo | eliminado")
    created_at: str = Field(..., description="Fecha y hora de creación (ISO 8601)")


class PagoDetailResponse(PagoResponse):
    distribuciones: list[PagoItemResponse] = Field(
        ..., description="Líneas de distribución del pago"
    )


class EntregaPendienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ID de la entrega")
    numero: int = Field(..., description="Número secuencial de la entrega")
    snap_nombre: str = Field(
        ..., description="Nombre del destinatario (snapshot inmutable)"
    )
    total_entrega: Decimal = Field(..., description="Valor total de la entrega")
    saldo_pendiente: Decimal = Field(
        ..., description="Saldo no cobrado; nunca negativo"
    )
