"""Integration tests for Kardex endpoints."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kardex import KardexMovimiento
from app.models.producto import Producto
from app.models.xml_item import XmlItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clave(n: int) -> str:
    return f"5{n:04d}" + "0" * 44  # 49 chars, unique to kardex tests (prefix 5)


def _xml_bytes(
    clave: str,
    *,
    ambiente: int = 2,
    codigo: str = "PROD_KARDEX_TEST",
    cantidad: str = "4.0000",
    precio_unit: str = "25.0000",
    precio_total: str = "100.00",
    peso: str = "2.0",
) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<factura version="2.1.0" id="comprobante">
  <infoTributaria>
    <ambiente>{ambiente}</ambiente>
    <tipoEmision>1</tipoEmision>
    <razonSocial>EMPRESA TEST SA</razonSocial>
    <ruc>1790012345001</ruc>
    <claveAcceso>{clave}</claveAcceso>
    <estab>001</estab>
    <ptoEmi>001</ptoEmi>
    <secuencial>000000001</secuencial>
  </infoTributaria>
  <infoFactura>
    <fechaEmision>15/01/2024</fechaEmision>
    <identificacionComprador>0912345678001</identificacionComprador>
    <razonSocialComprador>CLIENTE TEST SA</razonSocialComprador>
    <totalSinImpuestos>{precio_total}</totalSinImpuestos>
    <totalDescuento>0.00</totalDescuento>
    <totalConImpuestos>
      <totalImpuesto>
        <codigo>2</codigo>
        <codigoPorcentaje>4</codigoPorcentaje>
        <baseImponible>{precio_total}</baseImponible>
        <valor>15.00</valor>
      </totalImpuesto>
    </totalConImpuestos>
    <importeTotal>115.00</importeTotal>
    <moneda>DOLAR</moneda>
  </infoFactura>
  <detalles>
    <detalle>
      <codigoPrincipal>{codigo}</codigoPrincipal>
      <descripcion>Producto kardex test</descripcion>
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
          <valor>15.00</valor>
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


async def _post_xml(
    client: AsyncClient, token: str, clave: str, **kwargs
) -> tuple[dict, int]:
    resp = await client.post(
        "/xmls",
        files={"file": ("factura.xml", _xml_bytes(clave, **kwargs), "text/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    return dict(resp.json()), resp.status_code


async def _ingresar(
    client: AsyncClient,
    token: str,
    xml_id: str,
    items: list[dict],
) -> tuple[dict | list, int]:
    resp = await client.post(
        f"/xmls/{xml_id}/ingresos",
        json={"items": items},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json(), resp.status_code


# ---------------------------------------------------------------------------
# POST /xmls/{id}/ingresos — contract tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingresar_payload_valido_201(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(1), codigo="K_VALID_01")
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    result, status = await _ingresar(
        test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 2}]
    )
    assert status == 201
    assert isinstance(result, list)
    assert len(result) == 1
    mov = result[0]
    assert mov["tipo"] == "ingreso"
    assert mov["origen"] == "xml"
    assert Decimal(str(mov["cantidad"])) == Decimal("2")
    assert "id" in mov


@pytest.mark.asyncio
async def test_ingresar_cantidad_mayor_pendiente_400(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(2), codigo="K_OVERQ_01")
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    _, status = await _ingresar(
        test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 999}]
    )
    assert status == 400


@pytest.mark.asyncio
async def test_ingresar_cantidad_cero_422(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(3), codigo="K_ZERO_01")
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    _, status = await _ingresar(
        test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 0}]
    )
    assert status == 422


@pytest.mark.asyncio
async def test_ingresar_cantidad_negativa_422(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(4), codigo="K_NEG_01")
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    _, status = await _ingresar(
        test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": -1}]
    )
    assert status == 422


@pytest.mark.asyncio
async def test_ingresar_items_vacio_422(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(5), codigo="K_EMPTY_01")
    xml_id = data["id"]

    _, status = await _ingresar(test_client, token, xml_id, [])
    assert status == 422


@pytest.mark.asyncio
async def test_ingresar_item_de_otro_xml_404(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    data_a, _ = await _post_xml(test_client, token, _clave(6), codigo="K_OTH_A")
    data_b, _ = await _post_xml(test_client, token, _clave(7), codigo="K_OTH_B")

    xml_a_id = data_a["id"]
    item_b_id = data_b["items"][0]["id"]  # item from XML B

    _, status = await _ingresar(
        test_client, token, xml_a_id, [{"xml_item_id": item_b_id, "cantidad": 1}]
    )
    assert status == 404


@pytest.mark.asyncio
async def test_ingresar_rol_lectura_403(test_client: AsyncClient) -> None:
    admin_token = await _admin_token(test_client)
    lectura_token = await _create_user_token(
        test_client, admin_token, "lectura_kardex_01@test.com", "lectura"
    )
    data, _ = await _post_xml(test_client, admin_token, _clave(8), codigo="K_403_01")
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    _, status = await _ingresar(
        test_client, lectura_token, xml_id, [{"xml_item_id": item_id, "cantidad": 1}]
    )
    assert status == 403


@pytest.mark.asyncio
async def test_ingresar_sin_auth_403(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(9), codigo="K_AUTH_01")
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    resp = await test_client.post(
        f"/xmls/{xml_id}/ingresos",
        json={"items": [{"xml_item_id": item_id, "cantidad": 1}]},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /kardex/productos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_listar_productos_200(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_listar_productos_sin_auth_403(test_client: AsyncClient) -> None:
    resp = await test_client.get("/kardex/productos")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /kardex/{producto_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_historial_producto_existente_200(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    codigo = "K_HIST_EXIST"
    data, _ = await _post_xml(test_client, token, _clave(20), codigo=codigo)
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    await _ingresar(
        test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 2}]
    )

    result = await db_session.execute(
        select(Producto).where(Producto.codigo_principal == codigo)
    )
    producto = result.scalar_one_or_none()
    assert producto is not None

    resp = await test_client.get(
        f"/kardex/{producto.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data_resp = resp.json()
    assert data_resp["total"] >= 1
    movs = data_resp["items"]
    assert len(movs) >= 1
    assert movs[0]["tipo"] == "ingreso"


@pytest.mark.asyncio
async def test_historial_producto_inexistente_404(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    fake_id = uuid.uuid4()
    resp = await test_client.get(
        f"/kardex/{fake_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_historial_filtro_fecha(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    codigo = "K_HIST_FECHA"
    data, _ = await _post_xml(test_client, token, _clave(21), codigo=codigo)
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    await _ingresar(
        test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 1}]
    )

    result = await db_session.execute(
        select(Producto).where(Producto.codigo_principal == codigo)
    )
    producto = result.scalar_one()

    resp_future = await test_client.get(
        f"/kardex/{producto.id}",
        params={"fecha_desde": "2099-01-01", "fecha_hasta": "2099-12-31"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_future.status_code == 200
    assert resp_future.json()["total"] == 0

    resp_past = await test_client.get(
        f"/kardex/{producto.id}",
        params={"fecha_desde": "2000-01-01", "fecha_hasta": "2099-12-31"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_past.status_code == 200
    assert resp_past.json()["total"] >= 1


# ---------------------------------------------------------------------------
# Business invariants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingreso_actualiza_saldo_producto(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    codigo = "K_SALDO_01"
    data, _ = await _post_xml(
        test_client, token, _clave(30), codigo=codigo,
        cantidad="4.0000", precio_unit="25.0000", precio_total="100.00"
    )
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    result, status = await _ingresar(
        test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 4}]
    )
    assert status == 201
    assert isinstance(result, list)

    # Verify saldos via response payload (avoids db_session identity-map cache)
    movs = result
    # costo_unitario = 100.00 / 4 = 25.0; costo_total = 4 * 25 = 100.00
    assert Decimal(str(movs[0]["saldo_cantidad"])) == Decimal("4.0000")
    assert Decimal(str(movs[0]["saldo_valor"])) == Decimal("100.00")

    # Also verify DB via GET historial endpoint
    producto = (await db_session.execute(
        select(Producto).where(Producto.codigo_principal == codigo)
    )).scalar_one()
    assert producto.saldo_cantidad == Decimal("4.0000")
    assert producto.saldo_valor == Decimal("100.00")


@pytest.mark.asyncio
async def test_ingreso_parcial_actualiza_cantidades(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    codigo = "K_PARTIAL_01"
    data, _ = await _post_xml(test_client, token, _clave(31), codigo=codigo)
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    # Ingresar solo 3 de 4
    _, status = await _ingresar(
        test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 3}]
    )
    assert status == 201

    xml_item = (await db_session.execute(
        select(XmlItem).where(XmlItem.id == uuid.UUID(item_id))
    )).scalar_one()

    assert xml_item.cantidad_ingresada == Decimal("3.0000")
    assert xml_item.cantidad_pendiente == Decimal("1.0000")


@pytest.mark.asyncio
async def test_reingreso_crea_nuevo_movimiento(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    codigo = "K_REINGR_01"
    data, _ = await _post_xml(test_client, token, _clave(32), codigo=codigo)
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    await _ingresar(test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 2}])
    await _ingresar(test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 2}])

    result = await db_session.execute(
        select(KardexMovimiento)
        .join(Producto, KardexMovimiento.producto_id == Producto.id)
        .where(Producto.codigo_principal == codigo)
    )
    movimientos = result.scalars().all()
    assert len(movimientos) == 2

    xml_item = (await db_session.execute(
        select(XmlItem).where(XmlItem.id == uuid.UUID(item_id))
    )).scalar_one()
    assert xml_item.cantidad_ingresada == Decimal("4.0000")
    assert xml_item.cantidad_pendiente == Decimal("0.0000")


@pytest.mark.asyncio
async def test_item_con_pendiente_cero_no_aparece_en_pendientes(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(33), codigo="K_NOPEND_01")
    xml_id = data["id"]
    item_id = data["items"][0]["id"]

    # Ingresar todo → cantidad_pendiente = 0
    await _ingresar(test_client, token, xml_id, [{"xml_item_id": item_id, "cantidad": 4}])

    resp = await test_client.get(
        f"/xmls/{xml_id}/pendientes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_saldo_kardex_movimiento_acumulado(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Two sequential ingresos must carry accumulated balance on each movement."""
    token = await _admin_token(test_client)
    codigo = "K_SALDO_ACUM"

    # Upload two XMLs for the same product
    data1, _ = await _post_xml(
        test_client, token, _clave(34), codigo=codigo,
        cantidad="4.0000", precio_unit="25.0000", precio_total="100.00"
    )
    data2, _ = await _post_xml(
        test_client, token, _clave(35), codigo=codigo,
        cantidad="6.0000", precio_unit="10.0000", precio_total="60.00"
    )
    xml_id1 = data1["id"]
    xml_id2 = data2["id"]
    item_id1 = data1["items"][0]["id"]
    item_id2 = data2["items"][0]["id"]

    # Ingest all of first XML: +4 units, +100.00
    r1, _ = await _ingresar(
        test_client, token, xml_id1, [{"xml_item_id": item_id1, "cantidad": 4}]
    )
    # Ingest all of second XML: +6 units, +60.00
    r2, _ = await _ingresar(
        test_client, token, xml_id2, [{"xml_item_id": item_id2, "cantidad": 6}]
    )

    assert isinstance(r1, list) and isinstance(r2, list)

    mov1 = r1[0]
    mov2 = r2[0]

    assert Decimal(str(mov1["saldo_cantidad"])) == Decimal("4.0000")
    assert Decimal(str(mov1["saldo_valor"])) == Decimal("100.00")
    assert Decimal(str(mov2["saldo_cantidad"])) == Decimal("10.0000")
    assert Decimal(str(mov2["saldo_valor"])) == Decimal("160.00")
