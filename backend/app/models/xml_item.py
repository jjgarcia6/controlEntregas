import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.kardex import XmlItemIngreso
    from app.models.xml import Xml


class XmlItem(AuditMixin, Base):
    __tablename__ = "xml_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    xml_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("xmls.id"), nullable=False
    )
    codigo_principal: Mapped[str] = mapped_column(String(50), nullable=False)
    codigo_auxiliar: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    descripcion: Mapped[str] = mapped_column(String(300), nullable=False)
    cantidad_documento: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    descuento: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    precio_total_sin_imp: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tarifa_iva: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    valor_iva: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    peso_documento: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0")
    )
    peso_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0")
    )
    cantidad_ingresada: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0")
    )
    cantidad_pendiente: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    xml: Mapped["Xml"] = relationship("Xml", back_populates="items")
    ingresos: Mapped[list["XmlItemIngreso"]] = relationship(
        "XmlItemIngreso", back_populates="xml_item", lazy="select"
    )
