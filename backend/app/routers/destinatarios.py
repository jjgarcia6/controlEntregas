import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_rol
from app.dependencies.db import get_db
from app.models.usuario import Usuario
from app.schemas.destinatario import (
    DestinatarioCreate,
    DestinatarioResponse,
    DestinatarioUpdate,
)
from app.services import destinatario_service

router = APIRouter(prefix="/destinatarios", tags=["destinatarios"])

_lectura_roles = require_rol(["admin", "operador", "lectura"])
_operador_roles = require_rol(["admin", "operador"])


@router.get("", response_model=list[DestinatarioResponse])
async def listar(
    _: Usuario = Depends(_lectura_roles),
    session: AsyncSession = Depends(get_db),
) -> list[DestinatarioResponse]:
    return await destinatario_service.listar(session=session)


@router.get("/{identificacion}", response_model=DestinatarioResponse)
async def buscar_por_identificacion(
    identificacion: str,
    _: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> DestinatarioResponse:
    return await destinatario_service.buscar_por_identificacion(
        identificacion=identificacion, session=session
    )


@router.post("", response_model=DestinatarioResponse, status_code=201)
async def crear(
    body: DestinatarioCreate,
    current_user: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> DestinatarioResponse:
    async with session.begin_nested():
        return await destinatario_service.crear(
            body,
            usuario_id=current_user.id,
            session=session,
        )


@router.patch("/{id}", response_model=DestinatarioResponse)
async def actualizar(
    id: uuid.UUID,
    body: DestinatarioUpdate,
    current_user: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> DestinatarioResponse:
    async with session.begin_nested():
        return await destinatario_service.actualizar(
            id,
            body,
            usuario_id=current_user.id,
            session=session,
        )
