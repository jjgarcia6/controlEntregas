"""Integration tests for trazabilidad endpoints."""

import uuid
from typing import Dict

import pytest
from httpx import AsyncClient

from app.config import settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clave(n: int) -> str:
    return f"8{n:04d}" + "0" * 44  # prefix 8 for trazabilidad tests


def _xml_bytes(clave: str, codigo: str = "TRAZ_PROD_01") -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<factura version="2.1.0" id="comprobante">
  <infoTributaria>
    <ambiente>2</ambiente>
    <tipoEmision>1</tipoEmision>
    <razonSocial>EMPRESA TRAZ TEST SA</razonSocial>
    <ruc>1790099988001</ruc>
    <claveAcceso>{clave}</claveAcceso>
    <estab>001</estab>
    <ptoEmi>001</ptoEmi>
    <secuencial>000000001</secuencial>
  </infoTributaria>
  <infoFactura>
    <fechaEmision>10/01/2024</fechaEmision>
    <identificacionComprador>0912399678001</identificacionComprador>
    <razonSocialComprador>CLIENTE TRAZ TEST</razonSocialComprador>
    <totalSinImpuestos>100.00</totalSinImpuestos>
    <totalDescuento>0.00</totalDescuento>
    <totalConImpuestos>
      <totalImpuesto>
        <codigo>2</codigo>
        <codigoPorcentaje>4</codigoPorcentaje>
        <baseImponible>100.00</baseImponible>
        <valor>15.00</valor>
      </totalImpuesto>
    </totalConImpuestos>
    <importeTotal>115.00</importeTotal>
    <moneda>DOLAR</moneda>
  </infoFactura>
  <detalles>
    <detalle>
      <codigoPrincipal>{codigo}</codigoPrincipal>
      <descripcion>Producto trazabilidad test</descripcion>
      <cantidad>5.0000</cantidad>
      <precioUnitario>20.0000</precioUnitario>
      <descuento>0.00</descuento>
      <precioTotalSinImpuesto>100.00</precioTotalSinImpuesto>
      <detallesAdicionales/>
      <impuestos>
        <impuesto>
          <codigo>2</codigo>
          <codigoPorcentaje>4</codigoPorcentaje>
          <tarifa>15</tarifa>
          <baseImponible>100.00</baseImponible>
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
    return await _get_token(client, "admin@sistema.com", settings.ADMIN_PASSWORD)


async def _create_user_token(
    client: AsyncClient, admin_token: str, email: str, rol: str
) -> str:
    await client.post(
        "/usuarios",
        json={"email": email, "password": "Test1234!", "nombre": "Test", "rol": rol},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return await _get_token(client, email, "Test1234!")


async def _setup_chain(client: AsyncClient, token: str, seq: int) -> Dict[str, str]:
    """Creates XML → kardex ingreso → entrega → pago chain. Returns IDs."""
    xml_resp = await client.post(
        "/xmls",
        files={"file": ("factura.xml", _xml_bytes(_clave(seq)), "text/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert xml_resp.status_code == 201, xml_resp.json()
    xml = xml_resp.json()
    xml_item_id = xml["items"][0]["id"]

    await client.post(
        f"/xmls/{xml['id']}/ingresos",
        json={"items": [{"xml_item_id": xml_item_id, "cantidad": 5.0}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    prods_resp = await client.get(
        "/kardex/productos", headers={"Authorization": f"Bearer {token}"}
    )
    productos = prods_resp.json()["items"]
    prod = next(p for p in productos if p["codigo_principal"] == "TRAZ_PROD_01")

    dest_resp = await client.post(
        "/destinatarios",
        json={
            "nombre": f"Dest Traz {seq}",
            "identificacion": "1700000001001",
            "direccion": "Av. Test 123",
            "telefono": "0991234567",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dest_resp.status_code == 201, dest_resp.json()
    dest_id = dest_resp.json()["id"]

    entrega_resp = await client.post(
        "/entregas",
        json={
            "destinatario_id": dest_id,
            "items": [{"producto_id": prod["id"], "cantidad": 2.0}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert entrega_resp.status_code == 201, entrega_resp.json()
    entrega = entrega_resp.json()

    banco_resp = await client.post(
        "/bancos",
        json={"nombre": f"Banco Traz {seq}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    banco_id = banco_resp.json()["id"]

    pago_resp = await client.post(
        "/pagos",
        json={
            "numero_comprobante": f"001-001-00{seq:06d}",
            "fecha_pago": "2024-03-15",
            "banco_id": banco_id,
            "tipo_cuenta": "transferencia",
            "nombre_titular": "Titular Traz",
            "valor_total": float(entrega["total_entrega"]),
            "distribuciones": [
                {
                    "entrega_id": entrega["id"],
                    "monto_aplicado": float(entrega["total_entrega"]),
                }
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pago_resp.status_code == 201, pago_resp.json()
    pago = pago_resp.json()

    return {"xml_id": xml["id"], "entrega_id": entrega["id"], "pago_id": pago["id"]}


# ---------------------------------------------------------------------------
# GET /trazabilidad/xml/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_return_complete_tree_from_xml_when_xml_has_ingresos_entregas_and_pagos(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    ids = await _setup_chain(test_client, token, 1)

    resp = await test_client.get(
        f"/trazabilidad/xml/{ids['xml_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["xml"]["id"] == ids["xml_id"]
    assert len(data["ingresos_kardex"]) >= 1
    assert len(data["entregas"]) >= 1
    assert len(data["pagos"]) >= 1


@pytest.mark.asyncio
async def test_should_return_empty_lists_from_xml_when_no_entregas_exist(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    xml_resp = await test_client.post(
        "/xmls",
        files={
            "file": (
                "factura.xml",
                _xml_bytes(_clave(2), "TRAZ_NO_ENTREGA"),
                "text/xml",
            )
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert xml_resp.status_code == 201
    xml = xml_resp.json()
    # Ingresar al kardex but do NOT create an entrega
    await test_client.post(
        f"/xmls/{xml['id']}/ingresos",
        json={"items": [{"xml_item_id": xml["items"][0]["id"], "cantidad": 3.0}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await test_client.get(
        f"/trazabilidad/xml/{xml['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["entregas"] == []
    assert data["pagos"] == []


@pytest.mark.asyncio
async def test_should_return_404_from_xml_when_xml_id_does_not_exist(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        f"/trazabilidad/xml/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /trazabilidad/entrega/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_return_complete_tree_from_entrega_with_xmls_and_pagos(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    ids = await _setup_chain(test_client, token, 3)

    resp = await test_client.get(
        f"/trazabilidad/entrega/{ids['entrega_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["entrega"]["id"] == ids["entrega_id"]
    assert len(data["xmls_origen"]) >= 1
    assert len(data["pagos"]) >= 1


@pytest.mark.asyncio
async def test_should_return_404_from_entrega_when_entrega_id_does_not_exist(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        f"/trazabilidad/entrega/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /trazabilidad/pago/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_return_complete_tree_from_pago_with_entregas_and_xmls(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    ids = await _setup_chain(test_client, token, 4)

    resp = await test_client.get(
        f"/trazabilidad/pago/{ids['pago_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["pago"]["id"] == ids["pago_id"]
    assert len(data["distribuciones"]) >= 1
    assert len(data["distribuciones"][0]["xmls_origen"]) >= 1


@pytest.mark.asyncio
async def test_should_return_404_from_pago_when_pago_id_does_not_exist(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        f"/trazabilidad/pago/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_return_401_for_unauthenticated_request_to_trazabilidad(
    test_client: AsyncClient,
) -> None:
    resp = await test_client.get(f"/trazabilidad/xml/{uuid.uuid4()}")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_should_allow_lectura_role_to_access_trazabilidad(
    test_client: AsyncClient,
) -> None:
    admin_token = await _admin_token(test_client)
    lectura_token = await _create_user_token(
        test_client,
        admin_token,
        f"lectura_traz_{uuid.uuid4().hex[:6]}@test.com",
        "lectura",
    )
    resp = await test_client.get(
        f"/trazabilidad/xml/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {lectura_token}"},
    )
    # 404 is fine — the role has access but the entity doesn't exist
    assert resp.status_code in (404, 200)
