import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.xml_item import XmlItem


class Xml(AuditMixin, Base):
    __tablename__ = "xmls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clave_acceso: Mapped[str] = mapped_column(String(49), nullable=False, unique=True)
    ruc_emisor: Mapped[str] = mapped_column(String(13), nullable=False)
    razon_social_emisor: Mapped[str] = mapped_column(String(300), nullable=False)
    nombre_comercial: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    numero_factura: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_emision: Mapped[date] = mapped_column(Date, nullable=False)
    direccion_emisor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo_emision: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ambiente: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ruc_comprador: Mapped[str] = mapped_column(String(13), nullable=False)
    razon_social_comprador: Mapped[str] = mapped_column(String(300), nullable=False)
    direccion_comprador: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_sin_impuestos: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_descuento: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    subtotal_iva_0: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    subtotal_gravado: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    valor_iva: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    importe_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(10), nullable=False, default="DOLAR")
    xml_raw: Mapped[str] = mapped_column(Text, nullable=False)

    items: Mapped[list["XmlItem"]] = relationship(
        "XmlItem", back_populates="xml", lazy="selectin"
    )
