import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.db import get_db
from app.models.usuario import Usuario
from app.utils.exceptions import EntidadNoEncontrada, NoAutenticado, PermisoInsuficiente

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise NoAutenticado("Token de autenticación requerido")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise NoAutenticado("Token inválido: sin subject")
    except jwt.PyJWTError:
        raise NoAutenticado("Token inválido o expirado")

    user_id = uuid.UUID(user_id_str)
    result = await session.execute(
        select(Usuario).where(Usuario.id == user_id, Usuario.is_active.is_(True))
    )
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise EntidadNoEncontrada("Usuario no encontrado o inactivo")

    return usuario


def require_rol(roles: list[str]) -> Callable[..., Any]:
    async def dependency(
        current_user: Usuario = Depends(get_current_user),
    ) -> Usuario:
        if current_user.rol not in roles:
            raise PermisoInsuficiente(
                f"Se requiere uno de los roles: {', '.join(roles)}"
            )
        return current_user

    return dependency
