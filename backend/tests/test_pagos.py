"""Integration tests for Pagos endpoints."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.entrega import Entrega

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clave(n: int) -> str:
    return f"7{n:04d}" + "0" * 44  # prefix 7 for pagos tests


def _xml_bytes(
    clave: str,
    *,
    ambiente: int = 2,
    codigo: str = "PAG_PROD_TEST",
    cantidad: str = "10.0000",
    precio_unit: str = "50.0000",
    precio_total: str = "500.00",
) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<factura version="2.1.0" id="comprobante">
  <infoTributaria>
    <ambiente>{ambiente}</ambiente>
    <tipoEmision>1</tipoEmision>
    <razonSocial>EMPRESA PAGOS TEST SA</razonSocial>
    <ruc>1790099999001</ruc>
    <claveAcceso>{clave}</claveAcceso>
    <estab>001</estab>
    <ptoEmi>001</ptoEmi>
    <secuencial>000000001</secuencial>
  </infoTributaria>
  <infoFactura>
    <fechaEmision>15/01/2024</fechaEmision>
    <identificacionComprador>0912399678001</identificacionComprador>
    <razonSocialComprador>CLIENTE PAGOS TEST</razonSocialComprador>
    <totalSinImpuestos>{precio_total}</totalSinImpuestos>
    <totalDescuento>0.00</totalDescuento>
    <totalConImpuestos>
      <totalImpuesto>
        <codigo>2</codigo>
        <codigoPorcentaje>4</codigoPorcentaje>
        <baseImponible>{precio_total}</baseImponible>
        <valor>75.00</valor>
      </totalImpuesto>
    </totalConImpuestos>
    <importeTotal>575.00</importeTotal>
    <moneda>DOLAR</moneda>
  </infoFactura>
  <detalles>
    <detalle>
      <codigoPrincipal>{codigo}</codigoPrincipal>
      <descripcion>Producto pagos test</descripcion>
      <cantidad>{cantidad}</cantidad>
      <precioUnitario>{precio_unit}</precioUnitario>
      <descuento>0.00</descuento>
      <precioTotalSinImpuesto>{precio_total}</precioTotalSinImpuesto>
      <detallesAdicionales>
        <detAdicional nombre="Peso" valor="1.0"/>
      </detallesAdicionales>
      <impuestos>
        <impuesto>
          <codigo>2</codigo>
          <codigoPorcentaje>4</codigoPorcentaje>
          <tarifa>15</tarifa>
          <baseImponible>{precio_total}</baseImponible>
          <valor>75.00</valor>
        </impuesto>
      </impuestos>
    </detalle>
  </detalles>
</factura>""".encode()


async def _get_token(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    return str(resp.json()["token"])


async def _admin_token(client: AsyncClient) -> str:
    return await _get_token(client, "admin@sistema.com", settings.ADMIN_PASSWORD)


async def _create_user_token(
    client: AsyncClient, admin_token: str, email: str, rol: str
) -> str:
    await client.post(
        "/usuarios",
        json={
            "email": email,
            "password": "Test1234!",
            "nombre": "Test User",
            "rol": rol,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return await _get_token(client, email, "Test1234!")


async def _crear_banco(client: AsyncClient, token: str, nombre: str) -> dict:
    resp = await client.post(
        "/bancos",
        json={"nombre": nombre},
        headers={"Authorization": f"Bearer {token}"},
    )
    return dict(resp.json())


async def _crear_destinatario(
    client: AsyncClient, token: str, identificacion: str
) -> dict:
    resp = await client.post(
        "/destinatarios",
        json={
            "identificacion": identificacion,
            "nombre": f"Destinatario Pago {identificacion[:4]}",
            "direccion": "Av. Test 456",
            "telefono": "0991111222",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return dict(resp.json())


async def _post_xml(client: AsyncClient, token: str, clave: str, **kwargs) -> dict:
    resp = await client.post(
        "/xmls",
        files={"file": ("factura.xml", _xml_bytes(clave, **kwargs), "text/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    return dict(resp.json())


async def _ingresar(
    client: AsyncClient, token: str, xml_id: str, items: list[dict]
) -> list:
    resp = await client.post(
        f"/xmls/{xml_id}/ingresos",
        json={"items": items},
        headers={"Authorization": f"Bearer {token}"},
    )
    return list(resp.json())


async def _crear_entrega(
    client: AsyncClient, token: str, destinatario_id: str, items: list[dict]
) -> tuple[dict, int]:
    resp = await client.post(
        "/entregas",
        json={"destinatario_id": destinatario_id, "items": items},
        headers={"Authorization": f"Bearer {token}"},
    )
    return dict(resp.json()), resp.status_code


async def _setup_entrega_con_saldo(
    client: AsyncClient,
    token: str,
    seq: int,
    dest_id: str,
    codigo: str = "PAG_PROD_TEST",
    cantidad: str = "10.0000",
    precio_unit: str = "50.0000",
    precio_total: str = "500.00",
) -> tuple[dict, str]:
    """Returns (entrega_data, producto_id)."""
    xml = await _post_xml(
        client,
        token,
        _clave(seq),
        codigo=codigo,
        cantidad=cantidad,
        precio_unit=precio_unit,
        precio_total=precio_total,
    )
    item_id = xml["items"][0]["id"]
    await _ingresar(
        client,
        token,
        xml["id"],
        [{"xml_item_id": item_id, "cantidad": float(cantidad)}],
    )

    resp = await client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    productos = resp.json()["items"]
    prod = next(p for p in productos if p["codigo_principal"] == codigo)

    entrega, status = await _crear_entrega(
        client,
        token,
        dest_id,
        [{"producto_id": prod["id"], "cantidad": float(cantidad)}],
    )
    assert (
        status == 201
    ), f"_setup_entrega_con_saldo: expected 201, got {status}: {entrega}"
    return entrega, prod["id"]


async def _crear_pago(
    client: AsyncClient,
    token: str,
    banco_id: str,
    valor_total: float,
    distribuciones: list[dict],
    numero: str = "001-001-000000001",
    fecha: str = "2024-06-15",
) -> tuple[dict, int]:
    resp = await client.post(
        "/pagos",
        json={
            "numero_comprobante": numero,
            "fecha_pago": fecha,
            "banco_id": banco_id,
            "tipo_cuenta": "transferencia",
            "nombre_titular": "Titular Test",
            "valor_total": valor_total,
            "distribuciones": distribuciones,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return dict(resp.json()), resp.status_code


# ---------------------------------------------------------------------------
# POST /pagos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_create_pago_when_totals_match(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1700000001001")
    banco = await _crear_banco(
        test_client, token, f"Banco Pago Test {uuid.uuid4().hex[:6]}"
    )

    entrega, _ = await _setup_entrega_con_saldo(test_client, token, 1, dest["id"])

    saldo_antes = Decimal(str(entrega["saldo_pendiente"]))
    monto = float(saldo_antes)

    data, status = await _crear_pago(
        test_client,
        token,
        banco["id"],
        monto,
        [{"entrega_id": entrega["id"], "monto_aplicado": monto}],
    )

    assert status == 201
    assert data["estado"] == "activo"
    assert Decimal(str(data["valor_total"])) == saldo_antes
    assert Decimal(str(data["valor_aplicado"])) == saldo_antes
    assert len(data["distribuciones"]) == 1
    assert data["distribuciones"][0]["entrega_id"] == entrega["id"]

    # Verify saldo_pendiente was reduced in the DB
    result = await db_session.execute(
        select(Entrega).where(Entrega.id == uuid.UUID(entrega["id"]))
    )
    entrega_db = result.scalar_one()
    assert entrega_db.saldo_pendiente == Decimal("0")


@pytest.mark.asyncio
async def test_should_reject_pago_when_sum_does_not_match_total(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710000017001")
    banco = await _crear_banco(
        test_client, token, f"Banco Pago Test {uuid.uuid4().hex[:6]}"
    )

    entrega, _ = await _setup_entrega_con_saldo(test_client, token, 2, dest["id"])
    saldo = float(entrega["saldo_pendiente"])

    # valor_total = saldo, but distribute only half → sum mismatch
    data, status = await _crear_pago(
        test_client,
        token,
        banco["id"],
        saldo,
        [{"entrega_id": entrega["id"], "monto_aplicado": saldo / 2}],
    )

    assert status == 422
    assert "detail" in data


@pytest.mark.asyncio
async def test_should_reject_pago_when_monto_exceeds_saldo_pendiente(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710100015001")
    banco = await _crear_banco(
        test_client, token, f"Banco Pago Test {uuid.uuid4().hex[:6]}"
    )

    entrega, _ = await _setup_entrega_con_saldo(test_client, token, 3, dest["id"])
    saldo = float(entrega["saldo_pendiente"])
    exceso = saldo + 100.0

    data, status = await _crear_pago(
        test_client,
        token,
        banco["id"],
        exceso,
        [{"entrega_id": entrega["id"], "monto_aplicado": exceso}],
    )

    assert status == 422
    assert "detail" in data


@pytest.mark.asyncio
async def test_should_reject_pago_when_entrega_is_deleted(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1713175071001")
    banco = await _crear_banco(
        test_client, token, f"Banco Pago Test {uuid.uuid4().hex[:6]}"
    )

    entrega, _ = await _setup_entrega_con_saldo(test_client, token, 4, dest["id"])

    # Delete the entrega first (no payments, so deletion succeeds)
    del_resp = await test_client.delete(
        f"/entregas/{entrega['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204

    # Now try to create a pago for the deleted entrega
    data, status = await _crear_pago(
        test_client,
        token,
        banco["id"],
        100.0,
        [{"entrega_id": entrega["id"], "monto_aplicado": 100.0}],
    )

    assert status == 400
    assert "detail" in data


@pytest.mark.asyncio
async def test_should_return_403_when_lectura_creates_pago(
    test_client: AsyncClient,
) -> None:
    admin_token = await _admin_token(test_client)
    lectura_token = await _create_user_token(
        test_client, admin_token, f"lectura_{uuid.uuid4().hex[:6]}@test.com", "lectura"
    )
    banco = await _crear_banco(
        test_client, admin_token, f"Banco Pago Test {uuid.uuid4().hex[:6]}"
    )

    data, status = await _crear_pago(
        test_client,
        lectura_token,
        banco["id"],
        100.0,
        [{"entrega_id": str(uuid.uuid4()), "monto_aplicado": 100.0}],
    )

    assert status == 403


# ---------------------------------------------------------------------------
# DELETE /pagos/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_delete_pago_and_restore_saldo_pendiente(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1720000007001")
    banco = await _crear_banco(
        test_client, token, f"Banco Pago Test {uuid.uuid4().hex[:6]}"
    )

    entrega, _ = await _setup_entrega_con_saldo(test_client, token, 5, dest["id"])
    saldo_original = Decimal(str(entrega["saldo_pendiente"]))
    monto = float(saldo_original) / 2

    pago, _ = await _crear_pago(
        test_client,
        token,
        banco["id"],
        monto,
        [{"entrega_id": entrega["id"], "monto_aplicado": monto}],
    )
    assert pago.get("id")

    # Verify saldo was reduced
    result = await db_session.execute(
        select(Entrega).where(Entrega.id == uuid.UUID(entrega["id"]))
    )
    entrega_db = result.scalar_one()
    await db_session.refresh(entrega_db)
    assert entrega_db.saldo_pendiente == saldo_original - Decimal(str(monto))

    # Delete the pago
    del_resp = await test_client.delete(
        f"/pagos/{pago['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["estado"] == "eliminado"

    # Verify saldo was restored
    await db_session.refresh(entrega_db)
    assert entrega_db.saldo_pendiente == saldo_original


# ---------------------------------------------------------------------------
# GET /pagos/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_return_404_when_pago_not_found(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        f"/pagos/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /pagos — filter by fecha
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_list_pagos_filtered_by_fecha(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1700000027001")
    banco = await _crear_banco(
        test_client, token, f"Banco Pago Test {uuid.uuid4().hex[:6]}"
    )

    entrega, _ = await _setup_entrega_con_saldo(test_client, token, 6, dest["id"])
    monto = float(entrega["saldo_pendiente"])

    await _crear_pago(
        test_client,
        token,
        banco["id"],
        monto,
        [{"entrega_id": entrega["id"], "monto_aplicado": monto}],
        fecha="2024-06-15",
    )

    # Filter within range — should find the pago
    resp = await test_client.get(
        "/pagos",
        params={"fecha_desde": "2024-06-01", "fecha_hasta": "2024-06-30"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    # Filter outside range — should find nothing for this date
    resp2 = await test_client.get(
        "/pagos",
        params={"fecha_desde": "2020-01-01", "fecha_hasta": "2020-01-31"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0


# ---------------------------------------------------------------------------
# GET /entregas/pendientes — filter by q
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_list_entregas_pendientes_filtered_by_q(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1701000000001")

    await _setup_entrega_con_saldo(test_client, token, 7, dest["id"])

    # Buscar por nombre del destinatario (snap_nombre)
    nombre = dest["nombre"]
    resp = await test_client.get(
        "/entregas/pendientes",
        params={"q": nombre[:10]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(
        nombre[:10].lower() in item["snap_nombre"].lower() for item in data["items"]
    )

    # Non-matching query should return empty
    resp2 = await test_client.get(
        "/entregas/pendientes",
        params={"q": "XXXXNONEXISTENTXXXX"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0
