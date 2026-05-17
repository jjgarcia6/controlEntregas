import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_rol
from app.dependencies.db import get_db
from app.models.usuario import Usuario
from app.schemas.banco import BancoCreate, BancoResponse, BancoUpdate
from app.services import banco_service

router = APIRouter(prefix="/bancos", tags=["bancos"])

_lectura_roles = require_rol(["admin", "operador", "lectura"])
_operador_roles = require_rol(["admin", "operador"])
_admin_only = require_rol(["admin"])


@router.get("", response_model=list[BancoResponse])
async def listar(
    _: Usuario = Depends(_lectura_roles),
    session: AsyncSession = Depends(get_db),
) -> list[BancoResponse]:
    return await banco_service.listar(session=session)


@router.post("", response_model=BancoResponse, status_code=201)
async def crear(
    body: BancoCreate,
    current_user: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> BancoResponse:
    async with session.begin_nested():
        return await banco_service.crear(
            body,
            usuario_id=current_user.id,
            session=session,
        )


@router.patch("/{id}", response_model=BancoResponse)
async def actualizar(
    id: uuid.UUID,
    body: BancoUpdate,
    current_user: Usuario = Depends(_admin_only),
    session: AsyncSession = Depends(get_db),
) -> BancoResponse:
    async with session.begin_nested():
        return await banco_service.actualizar(
            id,
            body,
            usuario_id=current_user.id,
            session=session,
        )
