import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Index, Integer, Numeric, Sequence, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.destinatario import Destinatario
    from app.models.kardex import KardexMovimiento
    from app.models.producto import Producto


_numero_seq = Sequence("entregas_numero_seq")


class EstadoEntrega(str, enum.Enum):
    activa = "activa"
    eliminada = "eliminada"


class Entrega(AuditMixin, Base):
    __tablename__ = "entregas"
    __table_args__ = (
        Index("ix_entregas_destinatario_id", "destinatario_id"),
        Index("ix_entregas_estado", "estado"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero: Mapped[int] = mapped_column(
        Integer, _numero_seq, server_default=_numero_seq.next_value(), nullable=False, unique=True
    )
    destinatario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("destinatarios.id"), nullable=False
    )
    snap_identificacion: Mapped[str] = mapped_column(String(13), nullable=False)
    snap_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    snap_direccion: Mapped[str] = mapped_column(Text, nullable=False)
    snap_telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    comentarios: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_entrega: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    saldo_pendiente: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[EstadoEntrega] = mapped_column(
        SAEnum(EstadoEntrega, name="estado_entrega"), nullable=False, default=EstadoEntrega.activa
    )

    destinatario: Mapped["Destinatario"] = relationship("Destinatario", back_populates="entregas")
    items: Mapped[list["EntregaItem"]] = relationship(
        "EntregaItem", back_populates="entrega", lazy="select"
    )


class EntregaItem(AuditMixin, Base):
    __tablename__ = "entrega_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrega_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entregas.id"), nullable=False
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False
    )
    xml_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("xml_items.id"), nullable=False
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    peso_total: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    costo_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    kardex_movimiento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kardex_movimientos.id"), nullable=False, unique=True
    )

    entrega: Mapped["Entrega"] = relationship("Entrega", back_populates="items")
    producto: Mapped["Producto"] = relationship("Producto", back_populates="entrega_items")
    fifo_detalle: Mapped[list["EntregaItemFifoDetalle"]] = relationship(
        "EntregaItemFifoDetalle", back_populates="entrega_item", lazy="select"
    )
    kardex_movimiento: Mapped["KardexMovimiento"] = relationship(
        "KardexMovimiento", foreign_keys=[kardex_movimiento_id]
    )


class EntregaItemFifoDetalle(Base):
    """Inmutable — sin AuditMixin, sin soft delete. Solo lectura después de crear."""

    __tablename__ = "entrega_item_fifo_detalle"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrega_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entrega_items.id"), nullable=False
    )
    kardex_ingreso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kardex_movimientos.id"), nullable=False
    )
    cantidad_consumida: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    entrega_item: Mapped["EntregaItem"] = relationship(
        "EntregaItem", back_populates="fifo_detalle"
    )
    kardex_ingreso: Mapped["KardexMovimiento"] = relationship(
        "KardexMovimiento", foreign_keys=[kardex_ingreso_id]
    )
