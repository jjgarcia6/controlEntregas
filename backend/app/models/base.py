import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    # Nullable intencionalmente: el admin bootstrap del seed.py se crea antes
    # de que exista cualquier usuario en la BD. La spec original (PROYECTO_ESPECIFICACION.md
    # §"Esquema base de auditoría") decía NOT NULL, pero el caso de bootstrap obliga
    # a la excepción. Toda creación posterior al bootstrap debe completar este campo
    # a nivel servicio.
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("usuarios.id", use_alter=True, name="fk_created_by_usuarios"),
        nullable=True,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("usuarios.id", use_alter=True, name="fk_updated_by_usuarios"),
        nullable=True,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("usuarios.id", use_alter=True, name="fk_deleted_by_usuarios"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def soft_delete(self, usuario_id: uuid.UUID) -> None:
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = usuario_id
