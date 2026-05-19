import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entrega import Entrega, EstadoEntrega
from app.models.pago import EstadoPago, Pago, PagoEntrega
from app.schemas.common import PaginatedResponse
from app.schemas.pago import (
    PagoDetailResponse,
    PagoItemResponse,
    PagoRequest,
    PagoResponse,
)
from app.utils.audit import auditar
from app.utils.exceptions import (
    EntidadNoEncontrada,
    ValidacionDistribucion,
    ValidacionNegocio,
)


@auditar("CREATE", "pagos")
async def crear_pago(
    datos: PagoRequest,
    *,
    session: AsyncSession,
    usuario_id: uuid.UUID,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> Pago:
    # Sort IDs ascending to acquire locks in a consistent order and prevent deadlock
    # when two concurrent payments share the same set of entregas.
    ids_ordenados = sorted(item.entrega_id for item in datos.distribuciones)

    result = await session.execute(
        select(Entrega)
        .where(Entrega.id.in_(ids_ordenados))
        .with_for_update()
        .order_by(Entrega.id)
    )
    entregas = {e.id: e for e in result.scalars().all()}

    suma = Decimal("0")
    for item in datos.distribuciones:
        entrega = entregas.get(item.entrega_id)
        if entrega is None:
            raise EntidadNoEncontrada(
                f"Entrega {item.entrega_id} no encontrada")
        if not entrega.is_active or entrega.estado == EstadoEntrega.eliminada:
            raise ValidacionNegocio(
                f"No se puede aplicar un pago a una entrega eliminada (id={item.entrega_id})"
            )
        if item.monto_aplicado > entrega.saldo_pendiente:
            raise ValidacionDistribucion(
                f"El monto {item.monto_aplicado} supera el saldo pendiente "
                f"{entrega.saldo_pendiente} de la entrega #{entrega.numero}"
            )
        suma += item.monto_aplicado

    if suma != datos.valor_total:
        raise ValidacionDistribucion(
            f"La suma de distribuciones ({suma}) no coincide con el valor total ({datos.valor_total})"
        )

    pago = Pago(
        numero_comprobante=datos.numero_comprobante,
        fecha_pago=datos.fecha_pago,
        banco_id=datos.banco_id,
        tipo_cuenta=datos.tipo_cuenta,
        nombre_titular=datos.nombre_titular,
        valor_total=datos.valor_total,
        valor_aplicado=datos.valor_total,
        estado=EstadoPago.activo,
        created_by=usuario_id,
    )
    session.add(pago)
    await session.flush()

    for item in datos.distribuciones:
        entrega = entregas[item.entrega_id]
        entrega.saldo_pendiente -= item.monto_aplicado
        pago_entrega = PagoEntrega(
            pago_id=pago.id,
            entrega_id=item.entrega_id,
            monto_aplicado=item.monto_aplicado,
            created_by=usuario_id,
        )
        session.add(pago_entrega)

    await session.flush()
    return pago


@auditar("SOFT_DELETE", "pagos")
async def eliminar_pago(
    pago_id: uuid.UUID,
    *,
    session: AsyncSession,
    usuario_id: uuid.UUID,
    entidad_id: uuid.UUID | None = None,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> Pago:
    result = await session.execute(
        select(Pago)
        .where(Pago.id == pago_id, Pago.is_active.is_(True))
        .with_for_update()
    )
    pago = result.scalar_one_or_none()
    if pago is None:
        raise EntidadNoEncontrada("Pago no encontrado")

    for pe in pago.pago_entregas:
        if not pe.is_active:
            continue
        entrega_result = await session.execute(
            select(Entrega)
            .where(Entrega.id == pe.entrega_id, Entrega.is_active.is_(True))
            .with_for_update()
        )
        entrega = entrega_result.scalar_one_or_none()
        if entrega is not None:
            entrega.saldo_pendiente += pe.monto_aplicado

    pago.soft_delete(usuario_id)
    pago.estado = EstadoPago.eliminado
    await session.flush()
    return pago


async def listar_pagos(
    session: AsyncSession,
    page: int,
    page_size: int,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    banco_id: uuid.UUID | None = None,
    entrega_id: uuid.UUID | None = None,
) -> PaginatedResponse[PagoResponse]:
    filters: list[ColumnElement[bool]] = [Pago.is_active.is_(True)]

    if fecha_desde is not None:
        filters.append(Pago.fecha_pago >=
                       datetime.combine(fecha_desde, time.min))
    if fecha_hasta is not None:
        filters.append(Pago.fecha_pago <=
                       datetime.combine(fecha_hasta, time.max))
    if banco_id is not None:
        filters.append(Pago.banco_id == banco_id)
    if entrega_id is not None:
        filters.append(
            Pago.id.in_(
                select(PagoEntrega.pago_id).where(
                    PagoEntrega.entrega_id == entrega_id,
                    PagoEntrega.is_active.is_(True),
                )
            )
        )

    offset = (page - 1) * page_size

    count_result = await session.execute(
        select(func.count()).select_from(Pago).where(*filters)
    )
    total = int(count_result.scalar_one())

    result = await session.execute(
        select(Pago)
        .where(*filters)
        .order_by(Pago.fecha_pago.desc())
        .offset(offset)
        .limit(page_size)
    )
    pagos = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_pago_response(p) for p in pagos],
    )


async def obtener_detalle(pago_id: uuid.UUID, session: AsyncSession) -> Pago:
    result = await session.execute(
        select(Pago).where(Pago.id == pago_id, Pago.is_active.is_(True))
    )
    pago = result.scalar_one_or_none()
    if pago is None:
        raise EntidadNoEncontrada("Pago no encontrado")
    return pago


def _to_pago_response(pago: Pago) -> PagoResponse:
    return PagoResponse(
        id=pago.id,
        numero_comprobante=pago.numero_comprobante,
        fecha_pago=pago.fecha_pago,
        banco_id=pago.banco_id,
        banco_nombre=pago.banco.nombre,
        tipo_cuenta=pago.tipo_cuenta.value,
        nombre_titular=pago.nombre_titular,
        valor_total=pago.valor_total,
        valor_aplicado=pago.valor_aplicado,
        estado=pago.estado.value,
        created_at=pago.created_at.isoformat(),
    )


def _to_pago_detail_response(pago: Pago) -> PagoDetailResponse:
    return PagoDetailResponse(
        id=pago.id,
        numero_comprobante=pago.numero_comprobante,
        fecha_pago=pago.fecha_pago,
        banco_id=pago.banco_id,
        banco_nombre=pago.banco.nombre,
        tipo_cuenta=pago.tipo_cuenta.value,
        nombre_titular=pago.nombre_titular,
        valor_total=pago.valor_total,
        valor_aplicado=pago.valor_aplicado,
        estado=pago.estado.value,
        created_at=pago.created_at.isoformat(),
        distribuciones=[
            PagoItemResponse(
                id=pe.id,
                entrega_id=pe.entrega_id,
                entrega_numero=pe.entrega.numero,
                monto_aplicado=pe.monto_aplicado,
            )
            for pe in pago.pago_entregas
            if pe.is_active
        ],
    )
