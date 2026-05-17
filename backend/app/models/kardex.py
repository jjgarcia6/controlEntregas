import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import TIMESTAMP, Enum as SAEnum, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.producto import Producto
    from app.models.xml_item import XmlItem


class TipoMovimiento(str, enum.Enum):
    ingreso = "ingreso"
    egreso = "egreso"


class OrigenMovimiento(str, enum.Enum):
    xml = "xml"
    entrega = "entrega"
    reversa_entrega = "reversa_entrega"


class KardexMovimiento(AuditMixin, Base):
    __tablename__ = "kardex_movimientos"
    __table_args__ = (
        Index("ix_kardex_movimientos_producto_fecha", "producto_id", "fecha_movimiento"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False
    )
    tipo: Mapped[TipoMovimiento] = mapped_column(
        SAEnum(TipoMovimiento, name="tipo_movimiento"), nullable=False
    )
    origen: Mapped[OrigenMovimiento] = mapped_column(
        SAEnum(OrigenMovimiento, name="origen_movimiento"), nullable=False
    )
    documento_origen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    fecha_movimiento: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    peso_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0")
    )
    peso_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0")
    )
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    costo_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    saldo_cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    saldo_valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    lote_fifo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kardex_movimientos.id"), nullable=True
    )

    producto: Mapped["Producto"] = relationship("Producto", back_populates="movimientos")
    xml_item_ingreso: Mapped[Optional["XmlItemIngreso"]] = relationship(
        "XmlItemIngreso", back_populates="kardex_movimiento", uselist=False
    )


class XmlItemIngreso(AuditMixin, Base):
    __tablename__ = "xml_item_ingresos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    xml_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("xml_items.id"), nullable=False
    )
    cantidad_ingresada: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    kardex_movimiento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kardex_movimientos.id"), nullable=False, unique=True
    )

    xml_item: Mapped["XmlItem"] = relationship("XmlItem", back_populates="ingresos")
    kardex_movimiento: Mapped["KardexMovimiento"] = relationship(
        "KardexMovimiento", back_populates="xml_item_ingreso"
    )
