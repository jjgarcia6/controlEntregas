import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.producto import Producto
from app.models.xml import Xml
from app.models.xml_item import XmlItem
from app.schemas.common import PaginatedResponse
from app.schemas.xml import (
    XmlItemPreviewResponse,
    XmlListItem,
    XmlPreviewResponse,
)
from app.services import xml_parser_service
from app.utils.audit import auditar
from app.utils.exceptions import ConflictoUnicidad, EntidadNoEncontrada


async def preview(xml_content: str) -> XmlPreviewResponse:
    parsed = xml_parser_service.parsear(xml_content)
    return XmlPreviewResponse(
        clave_acceso=parsed.clave_acceso,
        ruc_emisor=parsed.ruc_emisor,
        razon_social_emisor=parsed.razon_social_emisor,
        nombre_comercial=parsed.nombre_comercial,
        numero_factura=parsed.numero_factura,
        fecha_emision=parsed.fecha_emision,
        direccion_emisor=parsed.direccion_emisor,
        tipo_emision=parsed.tipo_emision,
        ambiente=parsed.ambiente,
        ruc_comprador=parsed.ruc_comprador,
        razon_social_comprador=parsed.razon_social_comprador,
        direccion_comprador=parsed.direccion_comprador,
        total_sin_impuestos=parsed.total_sin_impuestos,
        total_descuento=parsed.total_descuento,
        subtotal_iva_0=parsed.subtotal_iva_0,
        subtotal_gravado=parsed.subtotal_gravado,
        valor_iva=parsed.valor_iva,
        importe_total=parsed.importe_total,
        moneda=parsed.moneda,
        items=[
            XmlItemPreviewResponse(
                codigo_principal=item.codigo_principal,
                codigo_auxiliar=item.codigo_auxiliar,
                descripcion=item.descripcion,
                cantidad_documento=item.cantidad_documento,
                precio_unitario=item.precio_unitario,
                descuento=item.descuento,
                precio_total_sin_imp=item.precio_total_sin_imp,
                tarifa_iva=item.tarifa_iva,
                valor_iva=item.valor_iva,
                peso_documento=item.peso_documento,
                peso_unitario=item.peso_unitario,
            )
            for item in parsed.items
        ],
    )


@auditar("CREATE", "xmls")
async def confirmar_ingreso(
    xml_content: str,
    *,
    usuario_id: uuid.UUID,
    session: AsyncSession,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> Xml:
    parsed = xml_parser_service.parsear(xml_content)

    existing = await session.execute(
        select(Xml).where(
            Xml.clave_acceso == parsed.clave_acceso,
            Xml.is_active.is_(True),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictoUnicidad("Ya existe un XML con esa clave de acceso")

    xml = Xml(
        clave_acceso=parsed.clave_acceso,
        ruc_emisor=parsed.ruc_emisor,
        razon_social_emisor=parsed.razon_social_emisor,
        nombre_comercial=parsed.nombre_comercial,
        numero_factura=parsed.numero_factura,
        fecha_emision=parsed.fecha_emision,
        direccion_emisor=parsed.direccion_emisor,
        tipo_emision=parsed.tipo_emision,
        ambiente=parsed.ambiente,
        ruc_comprador=parsed.ruc_comprador,
        razon_social_comprador=parsed.razon_social_comprador,
        direccion_comprador=parsed.direccion_comprador,
        total_sin_impuestos=parsed.total_sin_impuestos,
        total_descuento=parsed.total_descuento,
        subtotal_iva_0=parsed.subtotal_iva_0,
        subtotal_gravado=parsed.subtotal_gravado,
        valor_iva=parsed.valor_iva,
        importe_total=parsed.importe_total,
        moneda=parsed.moneda,
        xml_raw=parsed.xml_raw,
        created_by=usuario_id,
    )
    session.add(xml)

    for item_data in parsed.items:
        xml_item = XmlItem(
            xml_id=xml.id,
            codigo_principal=item_data.codigo_principal,
            codigo_auxiliar=item_data.codigo_auxiliar,
            descripcion=item_data.descripcion,
            cantidad_documento=item_data.cantidad_documento,
            precio_unitario=item_data.precio_unitario,
            descuento=item_data.descuento,
            precio_total_sin_imp=item_data.precio_total_sin_imp,
            tarifa_iva=item_data.tarifa_iva,
            valor_iva=item_data.valor_iva,
            peso_documento=item_data.peso_documento,
            peso_unitario=item_data.peso_unitario,
            cantidad_ingresada=Decimal("0"),
            cantidad_pendiente=item_data.cantidad_documento,
            created_by=usuario_id,
        )
        xml.items.append(xml_item)

    for item_data in parsed.items:
        prod_result = await session.execute(
            select(Producto).where(
                Producto.codigo_principal == item_data.codigo_principal
            )
        )
        producto = prod_result.scalar_one_or_none()
        if producto is None:
            producto = Producto(
                codigo_principal=item_data.codigo_principal,
                descripcion=item_data.descripcion,
                peso_unitario=item_data.peso_unitario,
                created_by=usuario_id,
            )
            session.add(producto)
        else:
            producto.descripcion = item_data.descripcion
            producto.peso_unitario = item_data.peso_unitario
            producto.updated_by = usuario_id

    await session.flush()
    return xml


async def listar(
    page: int, page_size: int, session: AsyncSession
) -> PaginatedResponse[XmlListItem]:
    offset = (page - 1) * page_size

    count_result = await session.execute(
        select(func.count()).select_from(Xml).where(Xml.is_active.is_(True))
    )
    total: int = int(count_result.scalar_one())

    result = await session.execute(
        select(Xml)
        .where(Xml.is_active.is_(True))
        .order_by(Xml.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    xmls = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[XmlListItem.model_validate(x) for x in xmls],
    )


async def obtener_por_id(xml_id: uuid.UUID, session: AsyncSession) -> Xml:
    result = await session.execute(
        select(Xml).where(Xml.id == xml_id, Xml.is_active.is_(True))
    )
    xml = result.scalar_one_or_none()
    if xml is None:
        raise EntidadNoEncontrada("XML no encontrado")
    return xml


async def obtener_pendientes(
    xml_id: uuid.UUID, session: AsyncSession
) -> list[XmlItem]:
    xml_check = await session.execute(
        select(Xml).where(Xml.id == xml_id, Xml.is_active.is_(True))
    )
    if xml_check.scalar_one_or_none() is None:
        raise EntidadNoEncontrada("XML no encontrado")

    result = await session.execute(
        select(XmlItem).where(
            XmlItem.xml_id == xml_id,
            XmlItem.cantidad_pendiente > 0,
            XmlItem.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


