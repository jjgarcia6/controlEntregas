import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_rol
from app.dependencies.db import get_db
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.kardex import KardexMovimientoResponse, ProductoConSaldoResponse
from app.services import kardex_service

router = APIRouter(prefix="/kardex", tags=["kardex"])

_lectura_roles = require_rol(["admin", "operador", "lectura"])


@router.get("/productos", response_model=PaginatedResponse[ProductoConSaldoResponse])
async def obtener_productos_con_saldo(
    page: int = 1,
    page_size: int = 20,
    _: Usuario = Depends(_lectura_roles),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ProductoConSaldoResponse]:
    return await kardex_service.obtener_productos_con_saldo(
        session=session, page=page, page_size=page_size
    )


@router.get("/{producto_id}", response_model=PaginatedResponse[KardexMovimientoResponse])
async def obtener_historial(
    producto_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    _: Usuario = Depends(_lectura_roles),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[KardexMovimientoResponse]:
    return await kardex_service.obtener_historial(
        producto_id=producto_id,
        session=session,
        page=page,
        page_size=page_size,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
