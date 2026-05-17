import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_rol
from app.dependencies.db import get_db
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.entrega import EntregaListItemResponse, EntregaRequest, EntregaResponse
from app.services import entrega_service

router = APIRouter(prefix="/entregas", tags=["entregas"])

_lectura_roles = require_rol(["admin", "operador", "lectura"])
_operador_roles = require_rol(["admin", "operador"])


@router.post("", response_model=EntregaResponse, status_code=201)
async def crear_entrega(
    body: EntregaRequest,
    current_user: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> EntregaResponse:
    async with session.begin_nested():
        entrega = await entrega_service.crear_entrega(
            body,
            session=session,
            usuario_id=current_user.id,
        )
    entrega = await entrega_service.obtener_entrega(entrega.id, session)
    return entrega_service._to_entrega_response(entrega)


@router.get("", response_model=PaginatedResponse[EntregaListItemResponse])
async def listar_entregas(
    destinatario_id: uuid.UUID | None = None,
    estado: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    page: int = 1,
    page_size: int = 20,
    _: Usuario = Depends(_lectura_roles),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[EntregaListItemResponse]:
    return await entrega_service.listar_entregas(
        session=session,
        page=page,
        page_size=page_size,
        destinatario_id=destinatario_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{id}", response_model=EntregaResponse)
async def obtener_entrega(
    id: uuid.UUID,
    _: Usuario = Depends(_lectura_roles),
    session: AsyncSession = Depends(get_db),
) -> EntregaResponse:
    entrega = await entrega_service.obtener_entrega(entrega_id=id, session=session)
    return entrega_service._to_entrega_response(entrega)


@router.delete("/{id}", status_code=204)
async def eliminar_entrega(
    id: uuid.UUID,
    current_user: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> None:
    async with session.begin_nested():
        await entrega_service.eliminar_entrega(
            id,
            session=session,
            usuario_id=current_user.id,
        )
