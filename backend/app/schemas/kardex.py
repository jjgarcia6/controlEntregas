import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KardexIngresoItemRequest(BaseModel):
    xml_item_id: uuid.UUID = Field(..., description="ID del xml_item a ingresar al Kardex")
    cantidad: Decimal = Field(
        ..., gt=0, decimal_places=4, description="Cantidad a ingresar. Debe ser mayor a 0 y no superar cantidad_pendiente"
    )


class KardexIngresoRequest(BaseModel):
    items: list[KardexIngresoItemRequest] = Field(
        ..., min_length=1, description="Lista de ítems a ingresar. Al menos uno requerido."
    )


class KardexMovimientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Identificador único del movimiento de Kardex")
    producto_id: uuid.UUID = Field(..., description="Producto afectado")
    tipo: str = Field(..., description="Tipo de movimiento: ingreso | egreso")
    origen: str = Field(..., description="Origen del movimiento: xml | entrega | reversa_entrega")
    documento_origen_id: uuid.UUID = Field(..., description="ID del documento origen (xml_item o entrega_item)")
    documento_origen_ref: str = Field(..., description="Referencia legible del documento origen")
    fecha_movimiento: datetime = Field(..., description="Timestamp del movimiento (ISO 8601)")
    cantidad: Decimal = Field(..., description="Unidades movidas")
    peso_unitario: Decimal = Field(..., description="Peso por unidad en kg")
    peso_total: Decimal = Field(..., description="Peso total del movimiento")
    costo_unitario: Decimal = Field(..., description="Costo por unidad calculado desde el XML")
    costo_total: Decimal = Field(..., description="Costo total del movimiento")
    saldo_cantidad: Decimal = Field(..., description="Saldo acumulado de unidades tras el movimiento")
    saldo_valor: Decimal = Field(..., description="Saldo acumulado de valor tras el movimiento")


class ProductoConSaldoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Identificador del producto")
    codigo_principal: str = Field(..., description="Código único del producto")
    descripcion: str = Field(..., description="Descripción del producto")
    unidad_medida: Optional[str] = Field(None, description="Unidad de medida (puede ser None)")
    peso_unitario: Decimal = Field(..., description="Peso unitario del último XML registrado")
    saldo_cantidad: Decimal = Field(..., description="Stock actual en unidades")
    saldo_valor: Decimal = Field(..., description="Valor del stock actual")
