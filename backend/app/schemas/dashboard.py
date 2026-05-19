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


class DashboardResponse(BaseModel):
    entregas_activas: int = Field(..., description="Número de entregas con estado activa.")
    saldo_pendiente_total: Decimal = Field(..., description="Suma de saldo_pendiente de todas las entregas activas.")
    total_facturado: Decimal = Field(..., description="Suma de total_entrega de todas las entregas activas.")
    total_cobrado: Decimal = Field(..., description="total_facturado - saldo_pendiente_total.")
    pagos_mes_actual: Decimal = Field(..., description="Suma de valor_total de pagos activos del mes en curso.")
    entregas_mas_antiguas: list[EntregaPendienteRow] = Field(
        ..., description="Las 5 entregas activas con saldo pendiente más antiguas."
    )
