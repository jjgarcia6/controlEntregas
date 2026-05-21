from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.banco import Banco
from app.models.entrega import Entrega, EstadoEntrega
from app.models.pago import EstadoPago, Pago
from app.models.xml_item import XmlItem
from app.schemas.dashboard import (
    DashboardResponse,
    EntregaPendienteRow,
    UltimaEntregaRow,
    UltimoPagoRow,
)


async def obtener_dashboard(session: AsyncSession) -> DashboardResponse:
    now = datetime.now(timezone.utc)
    inicio_mes = datetime(now.year, now.month, 1, tzinfo=None)

    agg_result = await session.execute(
        select(
            func.count(Entrega.id).label("entregas_activas"),
            func.coalesce(func.sum(Entrega.saldo_pendiente), Decimal("0")).label(
                "saldo_pendiente_total"
            ),
            func.coalesce(func.sum(Entrega.total_entrega), Decimal("0")).label(
                "total_facturado"
            ),
        ).where(
            Entrega.is_active.is_(True),
            Entrega.estado == EstadoEntrega.activa,
        )
    )
    row = agg_result.one()
    entregas_activas: int = int(row.entregas_activas)
    saldo_pendiente_total: Decimal = Decimal(str(row.saldo_pendiente_total))
    total_facturado: Decimal = Decimal(str(row.total_facturado))
    total_cobrado: Decimal = total_facturado - saldo_pendiente_total

    pagos_result = await session.execute(
        select(
            func.coalesce(func.sum(Pago.valor_total), Decimal("0")).label("pagos_mes")
        ).where(
            Pago.is_active.is_(True),
            Pago.estado == EstadoPago.activo,
            Pago.fecha_pago >= inicio_mes,
        )
    )
    pagos_mes_actual: Decimal = Decimal(str(pagos_result.scalar_one()))

    pendientes_result = await session.execute(
        select(Entrega)
        .where(
            Entrega.is_active.is_(True),
            Entrega.estado == EstadoEntrega.activa,
            Entrega.saldo_pendiente > 0,
        )
        .order_by(Entrega.created_at.asc())
        .limit(5)
    )
    entregas_pendientes = list(pendientes_result.scalars().all())

    xmls_pendientes_result = await session.execute(
        select(func.count(func.distinct(XmlItem.xml_id))).where(
            XmlItem.is_active.is_(True),
            XmlItem.cantidad_pendiente > 0,
        )
    )
    xmls_pendientes_count: int = int(xmls_pendientes_result.scalar_one())

    ultimas_entregas_result = await session.execute(
        select(Entrega)
        .where(Entrega.is_active.is_(True))
        .order_by(Entrega.created_at.desc())
        .limit(5)
    )
    ultimas_entregas_rows = list(ultimas_entregas_result.scalars().all())

    ultimos_pagos_result = await session.execute(
        select(
            Pago.id,
            Pago.numero_comprobante,
            Banco.nombre.label("nombre_banco"),
            Pago.valor_total,
            Pago.fecha_pago,
        )
        .join(Banco, Pago.banco_id == Banco.id)
        .where(Pago.is_active.is_(True))
        .order_by(Pago.created_at.desc())
        .limit(5)
    )
    ultimos_pagos_rows = ultimos_pagos_result.all()

    return DashboardResponse(
        entregas_activas=entregas_activas,
        saldo_pendiente_total=saldo_pendiente_total,
        total_facturado=total_facturado,
        total_cobrado=total_cobrado,
        pagos_mes_actual=pagos_mes_actual,
        entregas_mas_antiguas=[
            EntregaPendienteRow.model_validate(e) for e in entregas_pendientes
        ],
        xmls_pendientes_count=xmls_pendientes_count,
        ultimas_entregas=[
            UltimaEntregaRow.model_validate(e) for e in ultimas_entregas_rows
        ],
        ultimos_pagos=[
            UltimoPagoRow(
                id=r.id,
                numero_comprobante=r.numero_comprobante,
                nombre_banco=r.nombre_banco,
                valor_total=r.valor_total,
                fecha_pago=r.fecha_pago,
            )
            for r in ultimos_pagos_rows
        ],
    )
