import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.destinatario import Destinatario
from app.models.entrega import Entrega, EntregaItem, EntregaItemFifoDetalle, EstadoEntrega
from app.models.kardex import KardexMovimiento, OrigenMovimiento, TipoMovimiento
from app.models.producto import Producto
from app.schemas.common import PaginatedResponse
from app.schemas.entrega import (
    EntregaItemResponse,
    EntregaListItemResponse,
    EntregaRequest,
    EntregaResponse,
)
from app.utils.audit import auditar
from app.utils.exceptions import EntidadNoEncontrada, SaldoInsuficiente
from app.utils.fifo import LoteFIFO, calcular_consumo_fifo


@auditar("CREATE", "entregas")
async def crear_entrega(
    datos: EntregaRequest,
    *,
    session: AsyncSession,
    usuario_id: uuid.UUID,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> Entrega:
    dest_result = await session.execute(
        select(Destinatario).where(
            Destinatario.id == datos.destinatario_id,
            Destinatario.is_active.is_(True),
        )
    )
    destinatario = dest_result.scalar_one_or_none()
    if destinatario is None:
        raise EntidadNoEncontrada("Destinatario no encontrado")

    entrega = Entrega(
        destinatario_id=destinatario.id,
        snap_identificacion=destinatario.identificacion,
        snap_nombre=destinatario.nombre,
        snap_direccion=destinatario.direccion,
        snap_telefono=destinatario.telefono,
        comentarios=datos.comentarios,
        total_entrega=Decimal("0"),
        saldo_pendiente=Decimal("0"),
        estado=EstadoEntrega.activa,
        created_by=usuario_id,
    )
    session.add(entrega)
    await session.flush()

    total_entrega = Decimal("0")

    for item_req in datos.items:
        prod_result = await session.execute(
            select(Producto)
            .where(Producto.id == item_req.producto_id, Producto.is_active.is_(True))
            .with_for_update()
        )
        producto = prod_result.scalar_one_or_none()
        if producto is None:
            raise EntidadNoEncontrada(f"Producto {item_req.producto_id} no encontrado")

        if producto.saldo_cantidad < item_req.cantidad:
            raise SaldoInsuficiente(
                f"Stock insuficiente para '{producto.descripcion}': "
                f"disponible {producto.saldo_cantidad}, requerido {item_req.cantidad}"
            )

        lotes_result = await session.execute(
            select(KardexMovimiento)
            .where(
                KardexMovimiento.producto_id == producto.id,
                KardexMovimiento.tipo == TipoMovimiento.ingreso,
                KardexMovimiento.saldo_cantidad > 0,
                KardexMovimiento.is_active.is_(True),
            )
            .order_by(KardexMovimiento.fecha_movimiento.asc())
            .with_for_update()
        )
        lotes = list(lotes_result.scalars().all())

        lotes_fifo = [
            LoteFIFO(
                fecha=lote.fecha_movimiento,
                cantidad=lote.saldo_cantidad,
                costo_unitario=lote.costo_unitario,
                movimiento_id=lote.id,
            )
            for lote in lotes
        ]

        consumos = calcular_consumo_fifo(lotes_fifo, item_req.cantidad)

        lote_map = {lote.id: lote for lote in lotes}

        costo_total_item = sum(c.cantidad * c.costo_unitario for c in consumos)
        costo_unitario_promedio = costo_total_item / item_req.cantidad
        peso_total_item = item_req.cantidad * producto.peso_unitario

        xml_item_id = lote_map[consumos[0].movimiento_id].documento_origen_id

        running_saldo_cantidad = producto.saldo_cantidad
        running_saldo_valor = producto.saldo_valor
        primer_egreso: KardexMovimiento | None = None

        for consumo in consumos:
            lote = lote_map[consumo.movimiento_id]
            lote.saldo_cantidad = lote.saldo_cantidad - consumo.cantidad

            running_saldo_cantidad = running_saldo_cantidad - consumo.cantidad
            running_saldo_valor = running_saldo_valor - (consumo.cantidad * consumo.costo_unitario)

            egreso = KardexMovimiento(
                producto_id=producto.id,
                tipo=TipoMovimiento.egreso,
                origen=OrigenMovimiento.entrega,
                documento_origen_id=entrega.id,
                fecha_movimiento=datetime.now(timezone.utc),
                cantidad=consumo.cantidad,
                peso_unitario=producto.peso_unitario,
                peso_total=consumo.cantidad * producto.peso_unitario,
                costo_unitario=consumo.costo_unitario,
                costo_total=consumo.cantidad * consumo.costo_unitario,
                saldo_cantidad=running_saldo_cantidad,
                saldo_valor=running_saldo_valor,
                lote_fifo_id=lote.id,
                created_by=usuario_id,
            )
            session.add(egreso)
            await session.flush()

            if primer_egreso is None:
                primer_egreso = egreso

        if primer_egreso is None:
            raise SaldoInsuficiente("No se pudo calcular el consumo FIFO para el producto")

        entrega_item = EntregaItem(
            entrega_id=entrega.id,
            producto_id=producto.id,
            xml_item_id=xml_item_id,
            cantidad=item_req.cantidad,
            peso_total=peso_total_item,
            costo_unitario=costo_unitario_promedio,
            costo_total=costo_total_item,
            kardex_movimiento_id=primer_egreso.id,
            created_by=usuario_id,
        )
        session.add(entrega_item)
        await session.flush()

        for consumo in consumos:
            lote = lote_map[consumo.movimiento_id]
            detalle = EntregaItemFifoDetalle(
                entrega_item_id=entrega_item.id,
                kardex_ingreso_id=lote.id,
                cantidad_consumida=consumo.cantidad,
                costo_unitario=consumo.costo_unitario,
            )
            session.add(detalle)

        producto.saldo_cantidad = producto.saldo_cantidad - item_req.cantidad
        producto.saldo_valor = producto.saldo_valor - costo_total_item
        producto.updated_by = usuario_id

        total_entrega += costo_total_item

    entrega.total_entrega = total_entrega
    entrega.saldo_pendiente = total_entrega

    await session.flush()
    return entrega


async def listar_entregas(
    session: AsyncSession,
    page: int,
    page_size: int,
    destinatario_id: uuid.UUID | None = None,
    estado: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> PaginatedResponse[EntregaListItemResponse]:
    filters: list[ColumnElement[bool]] = [Entrega.is_active.is_(True)]

    if destinatario_id is not None:
        filters.append(Entrega.destinatario_id == destinatario_id)
    if estado is not None:
        filters.append(Entrega.estado == estado)
    if fecha_desde is not None:
        filters.append(
            Entrega.created_at
            >= datetime.combine(fecha_desde, time.min).replace(tzinfo=timezone.utc)
        )
    if fecha_hasta is not None:
        filters.append(
            Entrega.created_at
            <= datetime.combine(fecha_hasta, time.max).replace(tzinfo=timezone.utc)
        )

    offset = (page - 1) * page_size

    count_result = await session.execute(
        select(func.count()).select_from(Entrega).where(*filters)
    )
    total = int(count_result.scalar_one())

    result = await session.execute(
        select(Entrega)
        .where(*filters)
        .order_by(Entrega.numero.desc())
        .offset(offset)
        .limit(page_size)
    )
    entregas = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[EntregaListItemResponse.model_validate(e) for e in entregas],
    )


async def obtener_entrega(entrega_id: uuid.UUID, session: AsyncSession) -> Entrega:
    result = await session.execute(
        select(Entrega)
        .where(Entrega.id == entrega_id, Entrega.is_active.is_(True))
        .options(
            selectinload(Entrega.items)
            .selectinload(EntregaItem.fifo_detalle),
            selectinload(Entrega.items)
            .selectinload(EntregaItem.producto),
        )
    )
    entrega = result.scalar_one_or_none()
    if entrega is None:
        raise EntidadNoEncontrada("Entrega no encontrada")
    return entrega


@auditar("SOFT_DELETE", "entregas")
async def eliminar_entrega(
    entrega_id: uuid.UUID,
    *,
    session: AsyncSession,
    usuario_id: uuid.UUID,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> None:
    result = await session.execute(
        select(Entrega)
        .where(Entrega.id == entrega_id, Entrega.is_active.is_(True))
        .options(selectinload(Entrega.items).selectinload(EntregaItem.fifo_detalle))
        .with_for_update()
    )
    entrega = result.scalar_one_or_none()
    if entrega is None:
        raise EntidadNoEncontrada("Entrega no encontrada")

    # Fase 5 agrega pago_entregas; cuando exista, verificar aquí con:
    # SELECT pago_entregas WHERE entrega_id=... AND is_active=True
    # → EliminacionBloqueada con lista de comprobantes si los hay.

    for item in entrega.items:
        if not item.is_active:
            continue

        prod_result = await session.execute(
            select(Producto)
            .where(Producto.id == item.producto_id, Producto.is_active.is_(True))
            .with_for_update()
        )
        producto = prod_result.scalar_one_or_none()
        if producto is None:
            raise EntidadNoEncontrada(f"Producto {item.producto_id} no encontrado")

        running_saldo_cantidad = producto.saldo_cantidad
        running_saldo_valor = producto.saldo_valor

        for detalle in item.fifo_detalle:
            running_saldo_cantidad = running_saldo_cantidad + detalle.cantidad_consumida
            running_saldo_valor = running_saldo_valor + (
                detalle.cantidad_consumida * detalle.costo_unitario
            )

            reversa = KardexMovimiento(
                producto_id=producto.id,
                tipo=TipoMovimiento.egreso,
                origen=OrigenMovimiento.reversa_entrega,
                documento_origen_id=entrega.id,
                fecha_movimiento=datetime.now(timezone.utc),
                cantidad=detalle.cantidad_consumida,
                peso_unitario=producto.peso_unitario,
                peso_total=detalle.cantidad_consumida * producto.peso_unitario,
                costo_unitario=detalle.costo_unitario,
                costo_total=detalle.cantidad_consumida * detalle.costo_unitario,
                saldo_cantidad=running_saldo_cantidad,
                saldo_valor=running_saldo_valor,
                lote_fifo_id=detalle.kardex_ingreso_id,
                created_by=usuario_id,
            )
            session.add(reversa)

        producto.saldo_cantidad = running_saldo_cantidad
        producto.saldo_valor = running_saldo_valor
        producto.updated_by = usuario_id

    entrega.soft_delete(usuario_id)
    entrega.estado = EstadoEntrega.eliminada
    await session.flush()


def _to_entrega_response(entrega: Entrega) -> EntregaResponse:
    return EntregaResponse(
        id=entrega.id,
        numero=entrega.numero,
        destinatario_id=entrega.destinatario_id,
        snap_identificacion=entrega.snap_identificacion,
        snap_nombre=entrega.snap_nombre,
        snap_direccion=entrega.snap_direccion,
        snap_telefono=entrega.snap_telefono,
        comentarios=entrega.comentarios,
        total_entrega=entrega.total_entrega,
        saldo_pendiente=entrega.saldo_pendiente,
        estado=entrega.estado.value,
        items=[
            EntregaItemResponse(
                id=item.id,
                producto_id=item.producto_id,
                xml_item_id=item.xml_item_id,
                codigo_principal=item.producto.codigo_principal,
                descripcion=item.producto.descripcion,
                cantidad=item.cantidad,
                peso_total=item.peso_total,
                costo_unitario=item.costo_unitario,
                costo_total=item.costo_total,
            )
            for item in entrega.items
            if item.is_active
        ],
        created_at=entrega.created_at,
    )
