import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.audit_log import AuditLog
from app.models.usuario import Usuario
from app.schemas.auth import LoginResponse, RefreshResponse, UsuarioPublico
from app.utils.exceptions import PermisoInsuficiente
from app.utils.rate_limit import email_failure_tracker

# Pre-computed once at startup so nonexistent-user checks take the same time as real ones.
_DUMMY_HASH: bytes = bcrypt.hashpw(b"__dummy__", bcrypt.gensalt(rounds=12))


def _crear_jwt(usuario: Usuario) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRATION_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "rol": usuario.rol,
        "exp": expiration,
    }
    return str(
        jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    )


async def login(
    email: str,
    password: str,
    ip: str | None,
    user_agent: str | None,
    session: AsyncSession,
) -> LoginResponse:
    email_key = email.lower()
    if email_failure_tracker.is_blocked(email_key):
        raise PermisoInsuficiente("Credenciales inválidas")

    result = await session.execute(select(Usuario).where(Usuario.email == email))
    usuario = result.scalar_one_or_none()

    # Constant-time check: always run bcrypt to avoid timing attacks
    candidate = password.encode()

    if usuario is not None:
        stored = usuario.password_hash.encode()
        valid = bcrypt.checkpw(candidate, stored)
    else:
        bcrypt.checkpw(candidate, _DUMMY_HASH)
        valid = False

    if not valid or usuario is None or not usuario.is_active:
        email_failure_tracker.record_failure(email_key)
        raise PermisoInsuficiente("Credenciales inválidas")

    async with session.begin_nested():
        usuario.ultimo_login = datetime.now(timezone.utc)
        usuario.ip_ultimo_login = ip
        session.add(
            AuditLog(
                usuario_id=usuario.id,
                accion="LOGIN",
                entidad="usuarios",
                entidad_id=usuario.id,
                ip=ip,
                user_agent=user_agent,
            )
        )

    email_failure_tracker.reset(email_key)
    token = _crear_jwt(usuario)
    return LoginResponse(
        token=token,
        user=UsuarioPublico(
            id=usuario.id,
            email=usuario.email,
            nombre=usuario.nombre,
            rol=usuario.rol,
        ),
    )


async def refresh(token: str, session: AsyncSession) -> RefreshResponse:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            leeway=timedelta(seconds=settings.JWT_REFRESH_LEEWAY_SECONDS),
        )
    except jwt.PyJWTError:
        raise PermisoInsuficiente("Token inválido o expirado")

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise PermisoInsuficiente("Token inválido")

    result = await session.execute(
        select(Usuario).where(
            Usuario.id == uuid.UUID(user_id_str),
            Usuario.is_active.is_(True),
        )
    )
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise PermisoInsuficiente("Usuario inactivo o no encontrado")

    return RefreshResponse(token=_crear_jwt(usuario))
