import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_rol
from app.dependencies.db import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import PasswordUpdate, UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

_admin_only = require_rol(["admin"])


@router.get("", response_model=list[UsuarioResponse])
async def listar(
    _: Usuario = Depends(_admin_only),
    session: AsyncSession = Depends(get_db),
) -> list[UsuarioResponse]:
    return await usuario_service.listar(session=session)


@router.post("", response_model=UsuarioResponse, status_code=201)
async def crear(
    body: UsuarioCreate,
    current_user: Usuario = Depends(_admin_only),
    session: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    async with session.begin_nested():
        return await usuario_service.crear(
            body,
            usuario_id=current_user.id,
            session=session,
        )


@router.patch("/{id}", response_model=UsuarioResponse)
async def actualizar(
    id: uuid.UUID,
    body: UsuarioUpdate,
    current_user: Usuario = Depends(_admin_only),
    session: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    async with session.begin_nested():
        return await usuario_service.actualizar(
            id,
            body,
            usuario_id=current_user.id,
            session=session,
        )


@router.patch("/{id}/password", response_model=UsuarioResponse)
async def cambiar_password(
    id: uuid.UUID,
    body: PasswordUpdate,
    current_user: Usuario = Depends(_admin_only),
    session: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    async with session.begin_nested():
        return await usuario_service.cambiar_password(
            id,
            body,
            usuario_id=current_user.id,
            session=session,
        )


@router.delete("/{id}", response_model=UsuarioResponse)
async def desactivar(
    id: uuid.UUID,
    current_user: Usuario = Depends(_admin_only),
    session: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    async with session.begin_nested():
        return await usuario_service.desactivar(
            id,
            usuario_id=current_user.id,
            session=session,
        )
