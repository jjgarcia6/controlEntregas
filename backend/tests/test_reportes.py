"""Integration tests for /reportes endpoints."""

import uuid
from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clave(n: int) -> str:
    return f"9{n:04d}" + "0" * 44


def _xml_bytes(clave: str, codigo: str = "REP_PROD_01") -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<factura version="2.1.0" id="comprobante">
  <infoTributaria>
    <ambiente>2</ambiente>
    <tipoEmision>1</tipoEmision>
    <razonSocial>EMPRESA REPORTE TEST SA</razonSocial>
    <ruc>1790099999001</ruc>
    <claveAcceso>{clave}</claveAcceso>
    <estab>001</estab>
    <ptoEmi>001</ptoEmi>
    <secuencial>000000001</secuencial>
  </infoTributaria>
  <infoFactura>
    <fechaEmision>15/01/2024</fechaEmision>
    <identificacionComprador>0912399678001</identificacionComprador>
    <razonSocialComprador>CLIENTE REPORTE TEST</razonSocialComprador>
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
      <descripcion>Producto reporte test</descripcion>
      <cantidad>5.0000</cantidad>
      <precioUnitario>20.0000</precioUnitario>
      <descuento>0.00</descuento>
      <precioTotalSinImpuesto>100.00</precioTotalSinImpuesto>
      <detallesAdicionales>
        <detAdicional nombre="Peso" valor="1.0"/>
      </detallesAdicionales>
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


async def _auth(client: AsyncClient) -> dict[str, str]:
    token = await _admin_token(client)
    return {"Authorization": f"Bearer {token}"}


async def _upload_xml(
    client: AsyncClient,
    headers: Dict[str, str],
    clave: str,
    codigo: str = "REP_PROD_01",
) -> Dict[str, Any]:
    resp = await client.post(
        "/xmls",
        files={"file": ("factura.xml", _xml_bytes(clave, codigo), "text/xml")},
        headers=headers,
    )
    assert resp.status_code == 201
    return dict(resp.json())


async def _ingresar_kardex(
    client: AsyncClient, headers: Dict[str, str], xml_id: str, session: AsyncSession
) -> Tuple[str, str]:
    """Ingresa todos los ítems pendientes del XML al Kardex. Returns (xml_item_id, producto_id)."""
    resp = await client.get(f"/xmls/{xml_id}/pendientes", headers=headers)
    items = resp.json()
    assert len(items) > 0

    xml_item_id = items[0]["id"]
    cantidad = items[0]["cantidad_pendiente"]

    ingreso_resp = await client.post(
        f"/xmls/{xml_id}/ingresos",
        json={"items": [{"xml_item_id": xml_item_id, "cantidad": cantidad}]},
        headers=headers,
    )
    assert ingreso_resp.status_code == 201
    producto_id = ingreso_resp.json()[0]["producto_id"]
    return xml_item_id, producto_id


# ---------------------------------------------------------------------------
# Reporte XMLs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_return_xmls_report_filtered_by_date_range(
    test_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth(test_client)
    xml_data = await _upload_xml(test_client, headers, _clave(101))
    xml_id = xml_data["id"]

    resp = await test_client.get(
        "/reportes/xmls",
        params={
            "formato": "json",
            "fecha_desde": "2024-01-01",
            "fecha_hasta": "2024-12-31",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_xmls"] >= 1
    assert float(data["total_valor"]) >= 0
    ids = [f["xml_id"] for f in data["filas"]]
    assert xml_id in ids


@pytest.mark.asyncio
async def test_should_return_empty_xmls_report_when_no_data_in_range(
    test_client: AsyncClient,
) -> None:
    headers = await _auth(test_client)
    resp = await test_client.get(
        "/reportes/xmls",
        params={
            "formato": "json",
            "fecha_desde": "2000-01-01",
            "fecha_hasta": "2000-01-02",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filas"] == []
    assert data["total_xmls"] == 0


@pytest.mark.asyncio
async def test_should_return_kardex_report_for_given_product(
    test_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth(test_client)
    xml_data = await _upload_xml(test_client, headers, _clave(102), "REP_PROD_02")
    xml_id = xml_data["id"]
    _, producto_id = await _ingresar_kardex(test_client, headers, xml_id, db_session)

    resp = await test_client.get(
        "/reportes/kardex",
        params={"formato": "json", "producto_id": producto_id},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["producto_codigo"] != ""
    assert len(data["movimientos"]) >= 1
    # Verify ASC ordering
    fechas = [m["fecha_movimiento"] for m in data["movimientos"]]
    assert fechas == sorted(fechas)


@pytest.mark.asyncio
async def test_should_return_422_when_producto_id_missing_in_kardex_report(
    test_client: AsyncClient,
) -> None:
    headers = await _auth(test_client)
    resp = await test_client.get(
        "/reportes/kardex",
        params={"formato": "json"},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_should_return_404_when_producto_not_found_in_kardex_report(
    test_client: AsyncClient,
) -> None:
    headers = await _auth(test_client)
    resp = await test_client.get(
        "/reportes/kardex",
        params={"formato": "json", "producto_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_should_return_entregas_report_filtered_by_estado_activa(
    test_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth(test_client)

    resp = await test_client.get(
        "/reportes/entregas",
        params={"formato": "json", "estado": "activa"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # All rows must have estado == "activa"
    for fila in data["filas"]:
        assert fila["estado"] == "activa"
    # Invariant: total_cobrado + total_pendiente == total_valor
    total_cobrado = float(data["total_cobrado"])
    total_pendiente = float(data["total_pendiente"])
    total_valor = float(data["total_valor"])
    assert abs(total_cobrado + total_pendiente - total_valor) < 0.01


@pytest.mark.asyncio
async def test_should_return_pagos_report_filtered_by_banco(
    test_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth(test_client)

    # List bancos to get one
    resp_bancos = await test_client.get("/bancos", headers=headers)
    assert resp_bancos.status_code == 200
    bancos = resp_bancos.json()

    if not bancos:
        pytest.skip("No bancos available in test DB")

    banco_id = bancos[0]["id"]

    resp = await test_client.get(
        "/reportes/pagos",
        params={"formato": "json", "banco_id": banco_id},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # valor_total must equal sum of individual valor_totals
    suma = sum(float(f["valor_total"]) for f in data["filas"])
    assert abs(suma - float(data["valor_total"])) < 0.01


@pytest.mark.asyncio
async def test_should_return_pdf_with_correct_content_type(
    test_client: AsyncClient,
) -> None:
    headers = await _auth(test_client)
    for endpoint in ("xmls", "entregas", "pagos"):
        resp = await test_client.get(
            f"/reportes/{endpoint}",
            params={"formato": "pdf"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert "application/pdf" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_should_return_xlsx_with_correct_content_type(
    test_client: AsyncClient,
) -> None:
    headers = await _auth(test_client)
    for endpoint in ("xmls", "entregas", "pagos"):
        resp = await test_client.get(
            f"/reportes/{endpoint}",
            params={"formato": "xlsx"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_should_return_422_for_invalid_formato(
    test_client: AsyncClient,
) -> None:
    headers = await _auth(test_client)
    resp = await test_client.get(
        "/reportes/xmls",
        params={"formato": "csv"},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_should_return_401_for_unauthenticated_request(
    test_client: AsyncClient,
) -> None:
    resp = await test_client.get("/reportes/xmls")
    assert resp.status_code == 401
