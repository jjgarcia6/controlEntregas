import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, String
from sqlalchemy.dialects.postgresql import ENUM as PostgreSQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base

rol_usuario = PostgreSQLEnum("admin", "operador", "lectura", name="rol_usuario")


class Usuario(AuditMixin, Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    rol: Mapped[str] = mapped_column(rol_usuario, nullable=False)
    ultimo_login: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    ip_ultimo_login: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
