import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.banco import Banco
    from app.models.entrega import Entrega


class TipoCuenta(str, enum.Enum):
    corriente = "corriente"
    ahorros = "ahorros"
    transferencia = "transferencia"
    cheque = "cheque"
    efectivo = "efectivo"


class EstadoPago(str, enum.Enum):
    activo = "activo"
    eliminado = "eliminado"


class Pago(AuditMixin, Base):
    __tablename__ = "pagos"
    __table_args__ = (
        Index("ix_pagos_banco_id", "banco_id"),
        Index("ix_pagos_fecha_pago", "fecha_pago"),
        Index("ix_pagos_estado", "estado"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    numero_comprobante: Mapped[str] = mapped_column(
        String(100), nullable=False)
    fecha_pago: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    banco_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bancos.id"), nullable=False
    )
    tipo_cuenta: Mapped[TipoCuenta] = mapped_column(
        SAEnum(TipoCuenta, name="tipo_cuenta"), nullable=False
    )
    nombre_titular: Mapped[str] = mapped_column(String(255), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False)
    valor_aplicado: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    estado: Mapped[EstadoPago] = mapped_column(
        SAEnum(EstadoPago, name="estado_pago"),
        nullable=False,
        default=EstadoPago.activo,
    )

    banco: Mapped["Banco"] = relationship("Banco", lazy="selectin")
    pago_entregas: Mapped[list["PagoEntrega"]] = relationship(
        "PagoEntrega", back_populates="pago", lazy="selectin"
    )


class PagoEntrega(AuditMixin, Base):
    __tablename__ = "pago_entregas"
    __table_args__ = (
        UniqueConstraint("pago_id", "entrega_id",
                         name="uq_pago_entregas_pago_entrega"),
        Index("ix_pago_entregas_pago_id", "pago_id"),
        Index("ix_pago_entregas_entrega_id", "entrega_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pago_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pagos.id"), nullable=False
    )
    entrega_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entregas.id"), nullable=False
    )
    monto_aplicado: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False)

    pago: Mapped["Pago"] = relationship("Pago", back_populates="pago_entregas")
    entrega: Mapped["Entrega"] = relationship("Entrega", lazy="selectin")
