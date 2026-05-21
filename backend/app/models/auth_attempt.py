import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class AuthAttempt(Base):
    """
    Registro de intentos de autenticación.

    Esta tabla NO hereda de AuditMixin: es operacional, no de dominio de negocio.
    - Sin created_by: los intentos pueden venir de emails inexistentes o sin usuario asociado.
    - Sin soft delete: los registros se borran físicamente vía pg_cron tras 24h.
    - Sin foreign key a usuarios: precisamente queremos rastrear intentos sobre
      emails que pueden no existir.
    """

    __tablename__ = "auth_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
