import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class EntregaPendienteRow(BaseModel):
    id: uuid.UUID
    numero: int
    snap_nombre: str
    snap_identificacion: str
    total_entrega: Decimal
    saldo_pendiente: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class UltimaEntregaRow(BaseModel):
    id: uuid.UUID
    numero: int
    snap_nombre: str
    total_entrega: Decimal
    estado: str = Field(..., description="Estado actual de la entrega.")
    created_at: datetime

    model_config = {"from_attributes": True}


class UltimoPagoRow(BaseModel):
    id: uuid.UUID
    numero_comprobante: str = Field(..., description="Número de comprobante del pago.")
    nombre_banco: str = Field(
        ..., description="Nombre del banco resuelto desde la relación Banco."
    )
    valor_total: Decimal
    fecha_pago: datetime

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    entregas_activas: int = Field(
        ..., description="Número de entregas con estado activa."
    )
    saldo_pendiente_total: Decimal = Field(
        ..., description="Suma de saldo_pendiente de todas las entregas activas."
    )
    total_facturado: Decimal = Field(
        ..., description="Suma de total_entrega de todas las entregas activas."
    )
    total_cobrado: Decimal = Field(
        ..., description="total_facturado - saldo_pendiente_total."
    )
    pagos_mes_actual: Decimal = Field(
        ..., description="Suma de valor_total de pagos activos del mes en curso."
    )
    entregas_mas_antiguas: list[EntregaPendienteRow] = Field(
        ..., description="Las 5 entregas activas con saldo pendiente más antiguas."
    )
    xmls_pendientes_count: int = Field(
        ...,
        description="Cantidad de XMLs activos con al menos un ítem pendiente de kardex.",
    )
    ultimas_entregas: list[UltimaEntregaRow] = Field(
        ..., description="Las 5 entregas activas más recientes."
    )
    ultimos_pagos: list[UltimoPagoRow] = Field(
        ..., description="Los 5 pagos activos más recientes."
    )
