import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_rol
from app.dependencies.db import get_db
from app.models.usuario import Usuario
from app.schemas.common import DEFAULT_PAGE_SIZE, PaginatedResponse
from app.schemas.kardex import KardexIngresoRequest, KardexMovimientoResponse
from app.schemas.xml import (
    XmlItemPendienteResponse,
    XmlListItem,
    XmlPreviewResponse,
    XmlResponse,
)
from app.services import kardex_service, xml_service
from app.utils.uploads import read_xml_upload_as_text

router = APIRouter(prefix="/xmls", tags=["xmls"])

_lectura_roles = require_rol(["admin", "operador", "lectura"])
_operador_roles = require_rol(["admin", "operador"])


@router.post("/preview", response_model=XmlPreviewResponse)
async def preview(
    file: UploadFile = File(...),
    _: Usuario = Depends(_operador_roles),
) -> XmlPreviewResponse:
    content = await read_xml_upload_as_text(file)
    return await xml_service.preview(content)


@router.post("", response_model=XmlResponse, status_code=201)
async def confirmar_ingreso(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> XmlResponse:
    content = await read_xml_upload_as_text(file)
    async with session.begin_nested():
        xml = await xml_service.confirmar_ingreso(
            content,
            usuario_id=current_user.id,
            session=session,
        )
    return XmlResponse.model_validate(xml)


@router.get("", response_model=PaginatedResponse[XmlListItem])
async def listar(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    _: Usuario = Depends(_lectura_roles),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[XmlListItem]:
    return await xml_service.listar(page=page, page_size=page_size, session=session)


@router.get("/{id}", response_model=XmlResponse)
async def obtener_por_id(
    id: uuid.UUID,
    _: Usuario = Depends(_lectura_roles),
    session: AsyncSession = Depends(get_db),
) -> XmlResponse:
    xml = await xml_service.obtener_por_id(xml_id=id, session=session)
    return XmlResponse.model_validate(xml)


@router.post(
    "/{id}/ingresos", response_model=list[KardexMovimientoResponse], status_code=201
)
async def ingresar_items(
    id: uuid.UUID,
    body: KardexIngresoRequest,
    current_user: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> list[KardexMovimientoResponse]:
    async with session.begin_nested():
        movimientos = await kardex_service.ingresar_items(
            id,
            body.items,
            session=session,
            usuario_id=current_user.id,
        )
    return await kardex_service.build_movimiento_responses(movimientos, session)


@router.get("/{id}/pendientes", response_model=list[XmlItemPendienteResponse])
async def obtener_pendientes(
    id: uuid.UUID,
    _: Usuario = Depends(_operador_roles),
    session: AsyncSession = Depends(get_db),
) -> list[XmlItemPendienteResponse]:
    items = await xml_service.obtener_pendientes(xml_id=id, session=session)
    return [XmlItemPendienteResponse.model_validate(i) for i in items]
