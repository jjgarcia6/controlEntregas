import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.entrega import EntregaItem
    from app.models.kardex import KardexMovimiento


class Producto(AuditMixin, Base):
    __tablename__ = "productos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    codigo_principal: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(String(300), nullable=False)
    unidad_medida: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    peso_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0")
    )
    saldo_cantidad: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0")
    )
    saldo_valor: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )

    movimientos: Mapped[list["KardexMovimiento"]] = relationship(
        "KardexMovimiento", back_populates="producto", lazy="select"
    )
    entrega_items: Mapped[list["EntregaItem"]] = relationship(
        "EntregaItem", back_populates="producto", lazy="select"
    )
