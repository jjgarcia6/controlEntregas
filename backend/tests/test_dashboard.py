"""Integration tests for Dashboard endpoint."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def _admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/auth/login", json={"email": "admin@sistema.com", "password": "Admin1234!"}
    )
    return str(resp.json()["token"])


@pytest.mark.asyncio
async def test_dashboard_sin_autenticacion(test_client: AsyncClient) -> None:
    resp = await test_client.get("/dashboard")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_estructura_respuesta(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "entregas_activas" in data
    assert "saldo_pendiente_total" in data
    assert "total_facturado" in data
    assert "total_cobrado" in data
    assert "pagos_mes_actual" in data
    assert "entregas_mas_antiguas" in data
    assert isinstance(data["entregas_mas_antiguas"], list)


@pytest.mark.asyncio
async def test_dashboard_total_cobrado_es_diferencia(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()

    facturado = float(data["total_facturado"])
    pendiente = float(data["saldo_pendiente_total"])
    cobrado = float(data["total_cobrado"])
    assert abs(cobrado - (facturado - pendiente)) < 0.01


@pytest.mark.asyncio
async def test_dashboard_entregas_mas_antiguas_max_5(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert len(resp.json()["entregas_mas_antiguas"]) <= 5


@pytest.mark.asyncio
async def test_dashboard_entregas_mas_antiguas_schema(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    for fila in resp.json()["entregas_mas_antiguas"]:
        assert "id" in fila
        assert "numero" in fila
        assert "snap_nombre" in fila
        assert "snap_identificacion" in fila
        assert "total_entrega" in fila
        assert "saldo_pendiente" in fila
        assert "created_at" in fila


@pytest.mark.asyncio
async def test_dashboard_entregas_solo_con_saldo_pendiente(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)

    dest_resp = await test_client.post(
        "/destinatarios",
        json={
            "identificacion": "1713175071",
            "nombre": "Test Dash 6.1f",
            "direccion": "Av Test 123",
            "telefono": "0990000001",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dest_resp.status_code in (200, 201), dest_resp.text
    destinatario_id = dest_resp.json()["id"]

    # Insert an activa entrega with saldo_pendiente=0 (fully cobrada) and the
    # oldest possible created_at so it would appear first if the filter were wrong.
    entrega_id = uuid.uuid4()
    await db_session.execute(
        text("""
            INSERT INTO entregas (
                id, destinatario_id, snap_identificacion, snap_nombre,
                snap_direccion, snap_telefono, total_entrega, saldo_pendiente,
                estado, is_active, created_at, updated_at
            ) VALUES (
                :id, :destinatario_id, '1713175071', 'Test Dash 6.1f',
                'Av Test 123', '0990000001', 100.00, 0.00,
                'activa', true, '2020-01-01 00:00:00', '2020-01-01 00:00:00'
            )
        """),
        {"id": entrega_id, "destinatario_id": destinatario_id},
    )
    await db_session.flush()

    resp = await test_client.get(
        "/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    ids_en_resultado = [f["id"] for f in resp.json()["entregas_mas_antiguas"]]
    assert str(entrega_id) not in ids_en_resultado


@pytest.mark.asyncio
async def test_dashboard_pagos_mes_actual_estado_activo(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)

    baseline_resp = await test_client.get(
        "/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert baseline_resp.status_code == 200
    baseline = float(baseline_resp.json()["pagos_mes_actual"])

    banco_resp = await test_client.post(
        "/bancos",
        json={"nombre": f"Banco Test 6.1g {uuid.uuid4().hex[:6]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    banco_id = banco_resp.json()["id"]

    now = datetime.now(timezone.utc)
    last_month = (now.replace(day=1) - timedelta(days=1)).replace(tzinfo=None)
    now_naive = now.replace(tzinfo=None)

    # Pago activo del mes anterior — NO debe sumar en pagos_mes_actual
    await db_session.execute(
        text("""
            INSERT INTO pagos (
                id, banco_id, numero_comprobante, fecha_pago, tipo_cuenta,
                nombre_titular, valor_total, valor_aplicado, estado,
                is_active, created_at, updated_at
            ) VALUES (
                :id, :banco_id, 'COMP-6G-A', :fecha_pago, 'efectivo',
                'Test Titular', 500.00, 0.00, 'activo',
                true, NOW(), NOW()
            )
        """),
        {"id": uuid.uuid4(), "banco_id": banco_id, "fecha_pago": last_month},
    )

    # Pago eliminado del mes actual — NO debe sumar en pagos_mes_actual
    await db_session.execute(
        text("""
            INSERT INTO pagos (
                id, banco_id, numero_comprobante, fecha_pago, tipo_cuenta,
                nombre_titular, valor_total, valor_aplicado, estado,
                is_active, created_at, updated_at
            ) VALUES (
                :id, :banco_id, 'COMP-6G-B', :fecha_pago, 'efectivo',
                'Test Titular', 750.00, 0.00, 'eliminado',
                false, NOW(), NOW()
            )
        """),
        {"id": uuid.uuid4(), "banco_id": banco_id, "fecha_pago": now_naive},
    )
    await db_session.flush()

    resp = await test_client.get(
        "/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    after = float(resp.json()["pagos_mes_actual"])
    assert abs(after - baseline) < 0.01
