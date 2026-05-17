import uuid
from typing import Any

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario
from app.schemas.usuario import PasswordUpdate, UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.utils.audit import auditar
from app.utils.exceptions import ConflictoUnicidad, EntidadNoEncontrada


async def listar(session: AsyncSession) -> list[UsuarioResponse]:
    result = await session.execute(
        select(Usuario).where(Usuario.is_active.is_(True)).order_by(Usuario.nombre)
    )
    return [UsuarioResponse.model_validate(u) for u in result.scalars().all()]


@auditar("CREATE", "usuarios")
async def crear(
    datos: UsuarioCreate,
    *,
    usuario_id: uuid.UUID,
    session: AsyncSession,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> UsuarioResponse:
    email_str = str(datos.email)
    existing = await session.execute(
        select(Usuario).where(Usuario.email == email_str)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictoUnicidad(f"Ya existe un usuario con email '{email_str}'")

    password_hash = bcrypt.hashpw(datos.password.encode(), bcrypt.gensalt()).decode()
    nuevo = Usuario(
        email=email_str,
        password_hash=password_hash,
        nombre=datos.nombre,
        rol=datos.rol,
        created_by=usuario_id,
    )
    session.add(nuevo)
    await session.flush()
    return UsuarioResponse.model_validate(nuevo)


@auditar("UPDATE", "usuarios")
async def actualizar(
    usuario_id_param: uuid.UUID,
    datos: UsuarioUpdate,
    *,
    usuario_id: uuid.UUID,
    session: AsyncSession,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> UsuarioResponse:
    result = await session.execute(
        select(Usuario).where(
            Usuario.id == usuario_id_param, Usuario.is_active.is_(True)
        )
    )
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise EntidadNoEncontrada("Usuario no encontrado")

    if datos.email is not None:
        new_email = str(datos.email)
        if new_email != usuario.email:
            existing = await session.execute(
                select(Usuario).where(Usuario.email == new_email)
            )
            if existing.scalar_one_or_none() is not None:
                raise ConflictoUnicidad(
                    f"Ya existe un usuario con email '{new_email}'"
                )
        usuario.email = new_email

    if datos.nombre is not None:
        usuario.nombre = datos.nombre
    if datos.rol is not None:
        usuario.rol = datos.rol

    usuario.updated_by = usuario_id
    await session.flush()
    return UsuarioResponse.model_validate(usuario)


@auditar("UPDATE", "usuarios")
async def cambiar_password(
    usuario_id_param: uuid.UUID,
    datos: PasswordUpdate,
    *,
    usuario_id: uuid.UUID,
    session: AsyncSession,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> UsuarioResponse:
    result = await session.execute(
        select(Usuario).where(
            Usuario.id == usuario_id_param, Usuario.is_active.is_(True)
        )
    )
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise EntidadNoEncontrada("Usuario no encontrado")

    usuario.password_hash = bcrypt.hashpw(
        datos.nueva_password.encode(), bcrypt.gensalt()
    ).decode()
    usuario.updated_by = usuario_id
    await session.flush()
    return UsuarioResponse.model_validate(usuario)


@auditar("SOFT_DELETE", "usuarios")
async def desactivar(
    usuario_id_param: uuid.UUID,
    *,
    usuario_id: uuid.UUID,
    session: AsyncSession,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> UsuarioResponse:
    result = await session.execute(
        select(Usuario).where(
            Usuario.id == usuario_id_param, Usuario.is_active.is_(True)
        )
    )
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise EntidadNoEncontrada("Usuario no encontrado")

    usuario.soft_delete(usuario_id)
    await session.flush()
    return UsuarioResponse.model_validate(usuario)
