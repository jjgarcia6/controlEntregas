import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entrega import Entrega
from app.models.kardex import KardexMovimiento, OrigenMovimiento, TipoMovimiento, XmlItemIngreso
from app.models.producto import Producto
from app.models.xml import Xml
from app.models.xml_item import XmlItem
from app.schemas.common import PaginatedResponse
from app.schemas.kardex import KardexIngresoItemRequest, KardexMovimientoResponse, ProductoConSaldoResponse
from app.utils.audit import auditar
from app.utils.exceptions import EntidadNoEncontrada, ValidacionNegocio


@auditar("CREATE", "kardex_movimientos")
async def ingresar_items(
    xml_id: uuid.UUID,
    items: list[KardexIngresoItemRequest],
    *,
    session: AsyncSession,
    usuario_id: uuid.UUID,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> list[KardexMovimiento]:
    movimientos: list[KardexMovimiento] = []

    for item_req in items:
        xml_item_result = await session.execute(
            select(XmlItem)
            .where(XmlItem.id == item_req.xml_item_id, XmlItem.is_active.is_(True))
            .with_for_update()
        )
        xml_item = xml_item_result.scalar_one_or_none()

        if xml_item is None or xml_item.xml_id != xml_id:
            raise EntidadNoEncontrada(
                f"El ítem {item_req.xml_item_id} no pertenece al XML indicado"
            )

        if item_req.cantidad <= 0 or item_req.cantidad > xml_item.cantidad_pendiente:
            raise ValidacionNegocio(
                f"La cantidad {item_req.cantidad} es inválida para el ítem "
                f"{item_req.xml_item_id} (pendiente: {xml_item.cantidad_pendiente})"
            )

        producto_result = await session.execute(
            select(Producto)
            .where(
                Producto.codigo_principal == xml_item.codigo_principal,
                Producto.is_active.is_(True),
            )
            .with_for_update()
        )
        producto = producto_result.scalar_one_or_none()
        if producto is None:
            raise EntidadNoEncontrada(
                f"Producto {xml_item.codigo_principal} no encontrado"
            )

        costo_unitario: Decimal = (
            xml_item.precio_total_sin_imp / xml_item.cantidad_documento
        )
        peso_total: Decimal = item_req.cantidad * xml_item.peso_unitario
        costo_total: Decimal = item_req.cantidad * costo_unitario

        nuevo_saldo_cantidad = producto.saldo_cantidad + item_req.cantidad
        nuevo_saldo_valor = producto.saldo_valor + costo_total

        movimiento = KardexMovimiento(
            producto_id=producto.id,
            tipo=TipoMovimiento.ingreso,
            origen=OrigenMovimiento.xml,
            documento_origen_id=xml_item.id,
            fecha_movimiento=datetime.now(timezone.utc),
            cantidad=item_req.cantidad,
            peso_unitario=xml_item.peso_unitario,
            peso_total=peso_total,
            costo_unitario=costo_unitario,
            costo_total=costo_total,
            saldo_cantidad=nuevo_saldo_cantidad,
            saldo_valor=nuevo_saldo_valor,
            created_by=usuario_id,
        )
        session.add(movimiento)
        await session.flush()

        ingreso = XmlItemIngreso(
            xml_item_id=xml_item.id,
            cantidad_ingresada=item_req.cantidad,
            kardex_movimiento_id=movimiento.id,
            created_by=usuario_id,
        )
        session.add(ingreso)

        xml_item.cantidad_ingresada = xml_item.cantidad_ingresada + item_req.cantidad
        xml_item.cantidad_pendiente = xml_item.cantidad_pendiente - item_req.cantidad
        xml_item.updated_by = usuario_id

        producto.saldo_cantidad = nuevo_saldo_cantidad
        producto.saldo_valor = nuevo_saldo_valor
        producto.updated_by = usuario_id

        movimientos.append(movimiento)

    return movimientos


async def obtener_productos_con_saldo(
    session: AsyncSession,
    page: int,
    page_size: int,
) -> PaginatedResponse[ProductoConSaldoResponse]:
    offset = (page - 1) * page_size

    count_result = await session.execute(
        select(func.count()).select_from(Producto).where(Producto.is_active.is_(True))
    )
    total: int = int(count_result.scalar_one())

    result = await session.execute(
        select(Producto)
        .where(Producto.is_active.is_(True))
        .order_by(Producto.codigo_principal.asc())
        .offset(offset)
        .limit(page_size)
    )
    productos = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ProductoConSaldoResponse.model_validate(p) for p in productos],
    )


async def obtener_historial(
    producto_id: uuid.UUID,
    session: AsyncSession,
    page: int,
    page_size: int,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> PaginatedResponse[KardexMovimientoResponse]:
    producto_result = await session.execute(
        select(Producto).where(
            Producto.id == producto_id, Producto.is_active.is_(True)
        )
    )
    if producto_result.scalar_one_or_none() is None:
        raise EntidadNoEncontrada("Producto no encontrado")

    filters = [
        KardexMovimiento.producto_id == producto_id,
        KardexMovimiento.is_active.is_(True),
    ]
    if fecha_desde is not None:
        filters.append(
            KardexMovimiento.fecha_movimiento
            >= datetime.combine(fecha_desde, time.min).replace(tzinfo=timezone.utc)
        )
    if fecha_hasta is not None:
        filters.append(
            KardexMovimiento.fecha_movimiento
            <= datetime.combine(fecha_hasta, time.max).replace(tzinfo=timezone.utc)
        )

    offset = (page - 1) * page_size

    count_result = await session.execute(
        select(func.count())
        .select_from(KardexMovimiento)
        .where(*filters)
    )
    total: int = int(count_result.scalar_one())

    result = await session.execute(
        select(KardexMovimiento)
        .where(*filters)
        .order_by(KardexMovimiento.fecha_movimiento.asc())
        .offset(offset)
        .limit(page_size)
    )
    movimientos = result.scalars().all()

    ref_map: dict[uuid.UUID, str] = {}

    xml_item_ids = [
        m.documento_origen_id for m in movimientos if m.origen == OrigenMovimiento.xml
    ]
    if xml_item_ids:
        xml_ref_result = await session.execute(
            select(XmlItem.id, Xml.numero_factura)
            .join(Xml, XmlItem.xml_id == Xml.id)
            .where(XmlItem.id.in_(xml_item_ids))
        )
        for item_id, numero_factura in xml_ref_result.all():
            ref_map[item_id] = f"Factura {numero_factura}"

    entrega_ids = [
        m.documento_origen_id
        for m in movimientos
        if m.origen in (OrigenMovimiento.entrega, OrigenMovimiento.reversa_entrega)
    ]
    if entrega_ids:
        entrega_ref_result = await session.execute(
            select(Entrega.id, Entrega.numero).where(Entrega.id.in_(entrega_ids))
        )
        for entrega_id, numero in entrega_ref_result.all():
            ref_map[entrega_id] = f"N°{numero}"

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_mov_to_response(m, ref_map) for m in movimientos],
    )


def _mov_to_response(
    m: KardexMovimiento, ref_map: dict[uuid.UUID, str]
) -> KardexMovimientoResponse:
    raw = ref_map.get(m.documento_origen_id, str(m.documento_origen_id)[:8])
    if m.origen == OrigenMovimiento.reversa_entrega and raw.startswith("N°"):
        ref = f"Reversa {raw}"
    elif m.origen == OrigenMovimiento.entrega and raw.startswith("N°"):
        ref = f"Entrega {raw}"
    else:
        ref = raw
    return KardexMovimientoResponse(
        id=m.id,
        producto_id=m.producto_id,
        tipo=m.tipo.value,
        origen=m.origen.value,
        documento_origen_id=m.documento_origen_id,
        documento_origen_ref=ref,
        fecha_movimiento=m.fecha_movimiento,
        cantidad=m.cantidad,
        peso_unitario=m.peso_unitario,
        peso_total=m.peso_total,
        costo_unitario=m.costo_unitario,
        costo_total=m.costo_total,
        saldo_cantidad=m.saldo_cantidad,
        saldo_valor=m.saldo_valor,
    )
