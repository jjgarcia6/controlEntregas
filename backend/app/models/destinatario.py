import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import ENUM as PostgreSQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.entrega import Entrega

tipo_identificacion = PostgreSQLEnum("cedula", "ruc", name="tipo_identificacion")


class Destinatario(AuditMixin, Base):
    __tablename__ = "destinatarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tipo_identificacion: Mapped[str] = mapped_column(
        tipo_identificacion, nullable=False
    )
    identificacion: Mapped[str] = mapped_column(String(13), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    direccion: Mapped[str] = mapped_column(Text, nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    entregas: Mapped[list["Entrega"]] = relationship(
        "Entrega", back_populates="destinatario", lazy="select"
    )
