"""Integration tests for Entregas endpoints."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entrega import EntregaItem, EntregaItemFifoDetalle
from app.models.kardex import KardexMovimiento
from app.models.producto import Producto


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clave(n: int) -> str:
    return f"6{n:04d}" + "0" * 44  # unique prefix 6 for entregas tests


def _xml_bytes(
    clave: str,
    *,
    ambiente: int = 2,
    codigo: str = "ENT_PROD_TEST",
    cantidad: str = "20.0000",
    precio_unit: str = "10.0000",
    precio_total: str = "200.00",
    peso: str = "1.5",
) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<factura version="2.1.0" id="comprobante">
  <infoTributaria>
    <ambiente>{ambiente}</ambiente>
    <tipoEmision>1</tipoEmision>
    <razonSocial>EMPRESA ENTREGA TEST SA</razonSocial>
    <ruc>1790012345001</ruc>
    <claveAcceso>{clave}</claveAcceso>
    <estab>001</estab>
    <ptoEmi>001</ptoEmi>
    <secuencial>000000001</secuencial>
  </infoTributaria>
  <infoFactura>
    <fechaEmision>15/01/2024</fechaEmision>
    <identificacionComprador>0912345678001</identificacionComprador>
    <razonSocialComprador>CLIENTE ENTREGA TEST</razonSocialComprador>
    <totalSinImpuestos>{precio_total}</totalSinImpuestos>
    <totalDescuento>0.00</totalDescuento>
    <totalConImpuestos>
      <totalImpuesto>
        <codigo>2</codigo>
        <codigoPorcentaje>4</codigoPorcentaje>
        <baseImponible>{precio_total}</baseImponible>
        <valor>30.00</valor>
      </totalImpuesto>
    </totalConImpuestos>
    <importeTotal>230.00</importeTotal>
    <moneda>DOLAR</moneda>
  </infoFactura>
  <detalles>
    <detalle>
      <codigoPrincipal>{codigo}</codigoPrincipal>
      <descripcion>Producto entregas test</descripcion>
      <cantidad>{cantidad}</cantidad>
      <precioUnitario>{precio_unit}</precioUnitario>
      <descuento>0.00</descuento>
      <precioTotalSinImpuesto>{precio_total}</precioTotalSinImpuesto>
      <detallesAdicionales>
        <detAdicional nombre="Peso" valor="{peso}"/>
      </detallesAdicionales>
      <impuestos>
        <impuesto>
          <codigo>2</codigo>
          <codigoPorcentaje>4</codigoPorcentaje>
          <tarifa>15</tarifa>
          <baseImponible>{precio_total}</baseImponible>
          <valor>30.00</valor>
        </impuesto>
      </impuestos>
    </detalle>
  </detalles>
</factura>""".encode()


async def _get_token(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    return str(resp.json()["token"])


async def _admin_token(client: AsyncClient) -> str:
    return await _get_token(client, "admin@sistema.com", "Admin1234!")


async def _create_user_token(
    client: AsyncClient, admin_token: str, email: str, rol: str
) -> str:
    await client.post(
        "/usuarios",
        json={"email": email, "password": "Test1234!", "nombre": "Test User", "rol": rol},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return await _get_token(client, email, "Test1234!")


async def _crear_destinatario(client: AsyncClient, token: str, identificacion: str) -> dict:
    resp = await client.post(
        "/destinatarios",
        json={
            "identificacion": identificacion,
            "nombre": "Destinatario Test",
            "direccion": "Calle Test 123",
            "telefono": "0991234567",
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
    client: AsyncClient,
    token: str,
    destinatario_id: str,
    items: list[dict],
) -> tuple[dict, int]:
    resp = await client.post(
        "/entregas",
        json={"destinatario_id": destinatario_id, "items": items},
        headers={"Authorization": f"Bearer {token}"},
    )
    return dict(resp.json()), resp.status_code


async def _setup_producto_con_saldo(
    client: AsyncClient,
    token: str,
    clave: str,
    codigo: str,
    cantidad: str,
    precio_unit: str,
    precio_total: str,
) -> tuple[str, str]:
    """Ingresa XML y hace el ingreso al kardex. Retorna (xml_id, producto_id)."""
    xml = await _post_xml(
        client, token, clave, codigo=codigo,
        cantidad=cantidad, precio_unit=precio_unit, precio_total=precio_total
    )
    xml_id = xml["id"]
    item_id = xml["items"][0]["id"]
    await _ingresar(client, token, xml_id, [{"xml_item_id": item_id, "cantidad": float(cantidad)}])
    return xml_id, xml["items"][0]["id"]


# ---------------------------------------------------------------------------
# POST /entregas — contract tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crear_entrega_valida_201(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710000009001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(1), "ENT_V01", "20.0000", "10.0000", "200.00"
    )

    resp = await test_client.get(
        "/kardex/productos",
        headers={"Authorization": f"Bearer {token}"},
    )
    productos = resp.json()["items"]
    prod = next(p for p in productos if p["codigo_principal"] == "ENT_V01")

    data, status = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod["id"], "cantidad": 5}]
    )
    assert status == 201
    assert data["numero"] > 0
    assert data["estado"] == "activa"
    assert "items" in data
    assert len(data["items"]) == 1
    assert float(data["total_entrega"]) == pytest.approx(50.0)
    assert float(data["saldo_pendiente"]) == pytest.approx(50.0)


@pytest.mark.asyncio
async def test_crear_entrega_stock_insuficiente_400(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710010008001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(2), "ENT_V02", "5.0000", "10.0000", "50.00"
    )

    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_V02")

    _, status = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod["id"], "cantidad": 100}]
    )
    assert status == 400


@pytest.mark.asyncio
async def test_crear_entrega_items_vacios_422(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710020007001")
    resp = await test_client.post(
        "/entregas",
        json={"destinatario_id": dest["id"], "items": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_crear_entrega_cantidad_cero_422(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710030006001")
    resp = await test_client.post(
        "/entregas",
        json={
            "destinatario_id": dest["id"],
            "items": [{"producto_id": str(uuid.uuid4()), "cantidad": 0}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_crear_entrega_destinatario_inexistente_404(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    await _setup_producto_con_saldo(
        test_client, token, _clave(5), "ENT_V05", "10.0000", "10.0000", "100.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_V05")

    _, status = await _crear_entrega(
        test_client, str(uuid.uuid4()), str(uuid.uuid4()),
        [{"producto_id": prod["id"], "cantidad": 1}]
    )
    assert status == 401  # invalid token → 401


@pytest.mark.asyncio
async def test_crear_entrega_rol_lectura_403(test_client: AsyncClient) -> None:
    admin = await _admin_token(test_client)
    lectura = await _create_user_token(test_client, admin, "lectura_ent@test.com", "lectura")
    dest = await _crear_destinatario(test_client, admin, "1710050004001")
    resp = await test_client.post(
        "/entregas",
        json={"destinatario_id": dest["id"], "items": [{"producto_id": str(uuid.uuid4()), "cantidad": 1}]},
        headers={"Authorization": f"Bearer {lectura}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_crear_entrega_sin_autenticacion_401(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/entregas",
        json={"destinatario_id": str(uuid.uuid4()), "items": [{"producto_id": str(uuid.uuid4()), "cantidad": 1}]},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /entregas
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_listar_entregas_200(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/entregas", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_listar_entregas_filtro_estado(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/entregas?estado=activa", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["estado"] == "activa"


# ---------------------------------------------------------------------------
# GET /entregas/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_obtener_entrega_200(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710060003001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(7), "ENT_V07", "10.0000", "10.0000", "100.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_V07")

    created, _ = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod["id"], "cantidad": 3}]
    )
    entrega_id = created["id"]

    resp = await test_client.get(
        f"/entregas/{entrega_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == entrega_id
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_obtener_entrega_inexistente_404(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        f"/entregas/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /entregas/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_eliminar_entrega_sin_pagos_204(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710070002001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(8), "ENT_V08", "15.0000", "10.0000", "150.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_V08")
    prod_id = prod["id"]
    saldo_inicial = float(prod["saldo_cantidad"])

    created, _ = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod_id, "cantidad": 5}]
    )
    entrega_id = created["id"]

    resp = await test_client.delete(
        f"/entregas/{entrega_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 204

    prod_result = await db_session.execute(
        select(Producto).where(Producto.id == uuid.UUID(prod_id))
    )
    producto = prod_result.scalar_one_or_none()
    assert producto is not None
    assert float(producto.saldo_cantidad) == pytest.approx(saldo_inicial)


@pytest.mark.asyncio
async def test_eliminar_entrega_ya_eliminada_404(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710080001001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(9), "ENT_V09", "10.0000", "10.0000", "100.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_V09")

    created, _ = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod["id"], "cantidad": 2}]
    )
    entrega_id = created["id"]

    await test_client.delete(
        f"/entregas/{entrega_id}", headers={"Authorization": f"Bearer {token}"}
    )
    resp = await test_client.delete(
        f"/entregas/{entrega_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_eliminar_entrega_rol_lectura_403(test_client: AsyncClient) -> None:
    admin = await _admin_token(test_client)
    lectura = await _create_user_token(test_client, admin, "lectura_del@test.com", "lectura")
    resp = await test_client.delete(
        f"/entregas/{uuid.uuid4()}", headers={"Authorization": f"Bearer {lectura}"}
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Invariantes de negocio
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fifo_orden_cronologico(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verifica que los lotes más antiguos se consumen primero (FIFO)."""
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710090000001")

    # Lote A: 10 unidades a $5 c/u
    xml_a = await _post_xml(
        test_client, token, _clave(10), codigo="ENT_FIFO01",
        cantidad="10.0000", precio_unit="5.0000", precio_total="50.00"
    )
    await _ingresar(
        test_client, token, xml_a["id"],
        [{"xml_item_id": xml_a["items"][0]["id"], "cantidad": 10}]
    )

    # Lote B: 15 unidades a $8 c/u (más reciente, código diferente para nueva clave)
    xml_b = await _post_xml(
        test_client, token, _clave(11), codigo="ENT_FIFO01",
        cantidad="15.0000", precio_unit="8.0000", precio_total="120.00"
    )
    await _ingresar(
        test_client, token, xml_b["id"],
        [{"xml_item_id": xml_b["items"][0]["id"], "cantidad": 15}]
    )

    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_FIFO01")

    # Pide 12 unidades: consume 10 del lote A y 2 del lote B
    entrega_data, status = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod["id"], "cantidad": 12}]
    )
    assert status == 201

    # Verificar que los movimientos FIFO existen
    movimientos = await db_session.execute(
        select(KardexMovimiento).where(
            KardexMovimiento.documento_origen_id == uuid.UUID(entrega_data["id"])
        )
    )
    egresos = list(movimientos.scalars().all())
    assert len(egresos) == 2  # un egreso por lote consumido

    # Verificar fifo_detalle persiste aunque se elimine la entrega
    items_res = await db_session.execute(
        select(EntregaItem).where(
            EntregaItem.entrega_id == uuid.UUID(entrega_data["id"])
        )
    )
    entrega_items = list(items_res.scalars().all())
    assert len(entrega_items) == 1

    detalle_res = await db_session.execute(
        select(EntregaItemFifoDetalle).where(
            EntregaItemFifoDetalle.entrega_item_id == entrega_items[0].id
        )
    )
    detalles = list(detalle_res.scalars().all())
    assert len(detalles) == 2


@pytest.mark.asyncio
async def test_saldo_producto_reducido_tras_entrega(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710100007001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(12), "ENT_SALDO01", "30.0000", "10.0000", "300.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_SALDO01")
    prod_id = prod["id"]
    saldo_antes = Decimal(str(prod["saldo_cantidad"]))

    await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod_id, "cantidad": 12}]
    )

    prod_result = await db_session.execute(
        select(Producto).where(Producto.id == uuid.UUID(prod_id))
    )
    producto = prod_result.scalar_one()
    assert producto.saldo_cantidad == saldo_antes - Decimal("12")


@pytest.mark.asyncio
async def test_reversa_restaura_saldo_exactamente(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710110006001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(13), "ENT_REV01", "20.0000", "10.0000", "200.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_REV01")
    prod_id = prod["id"]

    # Saldo antes de la entrega
    prod_res = await db_session.execute(
        select(Producto).where(Producto.id == uuid.UUID(prod_id))
    )
    producto_antes = prod_res.scalar_one()
    saldo_antes_cantidad = producto_antes.saldo_cantidad
    saldo_antes_valor = producto_antes.saldo_valor

    # Crear entrega
    entrega_data, _ = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod_id, "cantidad": 8}]
    )
    await db_session.refresh(producto_antes)

    # Eliminar entrega (reversa)
    await test_client.delete(
        f"/entregas/{entrega_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # El saldo debe quedar exactamente igual al inicial
    await db_session.refresh(producto_antes)
    assert producto_antes.saldo_cantidad == saldo_antes_cantidad
    assert producto_antes.saldo_valor == pytest.approx(float(saldo_antes_valor))


@pytest.mark.asyncio
async def test_snapshot_destinatario_inmutable(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710120005001")
    dest_id = dest["id"]
    nombre_original = dest["nombre"]

    await _setup_producto_con_saldo(
        test_client, token, _clave(14), "ENT_SNAP01", "10.0000", "10.0000", "100.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_SNAP01")

    entrega_data, _ = await _crear_entrega(
        test_client, token, dest_id, [{"producto_id": prod["id"], "cantidad": 1}]
    )

    # Actualizar destinatario
    await test_client.patch(
        f"/destinatarios/{dest_id}",
        json={"nombre": "Nombre Completamente Distinto"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # El snapshot en la entrega debe conservar el nombre original
    resp = await test_client.get(
        f"/entregas/{entrega_data['id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.json()["snap_nombre"] == nombre_original


@pytest.mark.asyncio
async def test_numero_entrega_autoincremental(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710130004001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(15), "ENT_NUM01", "20.0000", "10.0000", "200.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_NUM01")

    e1, _ = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod["id"], "cantidad": 1}]
    )
    e2, _ = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod["id"], "cantidad": 1}]
    )

    assert e2["numero"] > e1["numero"]


@pytest.mark.asyncio
async def test_fifo_detalle_persiste_tras_eliminar_entrega(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    dest = await _crear_destinatario(test_client, token, "1710140003001")
    await _setup_producto_con_saldo(
        test_client, token, _clave(16), "ENT_PDET01", "10.0000", "10.0000", "100.00"
    )
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    prod = next(p for p in resp.json()["items"] if p["codigo_principal"] == "ENT_PDET01")

    entrega_data, _ = await _crear_entrega(
        test_client, token, dest["id"], [{"producto_id": prod["id"], "cantidad": 3}]
    )

    items_res = await db_session.execute(
        select(EntregaItem).where(
            EntregaItem.entrega_id == uuid.UUID(entrega_data["id"])
        )
    )
    item_ids = [i.id for i in items_res.scalars().all()]

    await test_client.delete(
        f"/entregas/{entrega_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    for item_id in item_ids:
        detalle_res = await db_session.execute(
            select(EntregaItemFifoDetalle).where(
                EntregaItemFifoDetalle.entrega_item_id == item_id
            )
        )
        detalles = list(detalle_res.scalars().all())
        assert len(detalles) > 0  # fifo_detalle persiste (inmutable)
