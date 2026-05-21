"""Integration tests for /xmls endpoints."""

import uuid
from decimal import Decimal
from typing import Any, Dict, Tuple

import pytest
from app.config import settings
from app.models.producto import Producto
from app.models.usuario import Usuario
from app.models.xml import Xml
from app.models.xml_item import XmlItem
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


def _clave(n: int) -> str:
    return f"{n:04d}" + "0" * 45  # 49 chars total


def _xml_bytes(
    clave: str,
    *,
    ambiente: int = 2,
    peso: str = "10.0",
    tarifa: str = "15",
    codigo: str = "PROD_XML_TEST",
    two_items: bool = False,
) -> bytes:
    second_item = (
        f"""
    <detalle>
      <codigoPrincipal>{codigo}_B</codigoPrincipal>
      <descripcion>Producto B</descripcion>
      <cantidad>2.0000</cantidad>
      <precioUnitario>10.0000</precioUnitario>
      <descuento>0.00</descuento>
      <precioTotalSinImpuesto>20.00</precioTotalSinImpuesto>
      <impuestos>
        <impuesto>
          <codigo>2</codigo>
          <codigoPorcentaje>4</codigoPorcentaje>
          <tarifa>{tarifa}</tarifa>
          <baseImponible>20.00</baseImponible>
          <valor>3.00</valor>
        </impuesto>
      </impuestos>
    </detalle>"""
        if two_items
        else ""
    )
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
      <descripcion>Producto de prueba</descripcion>
      <cantidad>4.0000</cantidad>
      <precioUnitario>25.0000</precioUnitario>
      <descuento>0.00</descuento>
      <precioTotalSinImpuesto>100.00</precioTotalSinImpuesto>
      <detallesAdicionales>
        <detAdicional nombre="Peso" valor="{peso}"/>
      </detallesAdicionales>
      <impuestos>
        <impuesto>
          <codigo>2</codigo>
          <codigoPorcentaje>4</codigoPorcentaje>
          <tarifa>{tarifa}</tarifa>
          <baseImponible>100.00</baseImponible>
          <valor>15.00</valor>
        </impuesto>
      </impuestos>
    </detalle>{second_item}
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


async def _post_xml(
    client: AsyncClient, token: str, clave: str, **kwargs: Any
) -> Tuple[Dict[str, Any], int]:
    resp = await client.post(
        "/xmls",
        files={"file": ("factura.xml", _xml_bytes(clave, **kwargs), "text/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    return dict(resp.json()), resp.status_code


# =============================================================
# Preview tests
# =============================================================


@pytest.mark.asyncio
async def test_preview_xml_valido_200(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/xmls/preview",
        files={"file": ("factura.xml", _xml_bytes(_clave(1)), "text/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["clave_acceso"] == _clave(1)
    assert len(data["items"]) == 1
    assert "importe_total" in data


@pytest.mark.asyncio
async def test_preview_xml_ambiente_1_400(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/xmls/preview",
        files={"file": ("factura.xml", _xml_bytes(_clave(2), ambiente=1), "text/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "ambiente" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_preview_xml_mal_formado_400(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/xmls/preview",
        files={"file": ("factura.xml", b"esto no es xml <<<<", "text/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_preview_xml_sin_auth_401(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/xmls/preview",
        files={"file": ("factura.xml", _xml_bytes(_clave(3)), "text/xml")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_preview_xml_rol_lectura_403(test_client: AsyncClient) -> None:
    admin_token = await _admin_token(test_client)
    lectura_token = await _create_user_token(
        test_client, admin_token, "lectura_xml_preview@test.com", "lectura"
    )
    resp = await test_client.post(
        "/xmls/preview",
        files={"file": ("factura.xml", _xml_bytes(_clave(4)), "text/xml")},
        headers={"Authorization": f"Bearer {lectura_token}"},
    )
    assert resp.status_code == 403


# =============================================================
# Confirmar tests
# =============================================================


@pytest.mark.asyncio
async def test_confirmar_xml_nuevo_201(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    data, status = await _post_xml(test_client, token, _clave(10))
    assert status == 201
    assert "id" in data
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert Decimal(str(item["cantidad_pendiente"])) == Decimal("4.0000")
    assert Decimal(str(item["cantidad_ingresada"])) == Decimal("0")


@pytest.mark.asyncio
async def test_confirmar_xml_crea_productos_nuevos(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    codigo = "PROD_NUEVO_INTEG"
    data, status = await _post_xml(test_client, token, _clave(11), codigo=codigo)
    assert status == 201

    result = await db_session.execute(
        select(Producto).where(Producto.codigo_principal == codigo)
    )
    producto = result.scalar_one_or_none()
    assert producto is not None
    assert producto.saldo_cantidad == Decimal("0")
    assert producto.saldo_valor == Decimal("0")


@pytest.mark.asyncio
async def test_confirmar_xml_actualiza_peso_producto_existente(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    codigo = "PROD_PESO_INTEG"

    await _post_xml(test_client, token, _clave(12), codigo=codigo, peso="10.0")
    await _post_xml(test_client, token, _clave(13), codigo=codigo, peso="20.0")

    result = await db_session.execute(
        select(Producto).where(Producto.codigo_principal == codigo)
    )
    producto = result.scalar_one_or_none()
    assert producto is not None
    # peso_unitario = 20.0 / 4.0 = 5.0
    assert producto.peso_unitario == Decimal("5.0000")


@pytest.mark.asyncio
async def test_confirmar_xml_clave_duplicada_409(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    _, first_status = await _post_xml(test_client, token, _clave(14))
    assert first_status == 201

    _, second_status = await _post_xml(test_client, token, _clave(14))
    assert second_status == 409


@pytest.mark.asyncio
async def test_confirmar_xml_ambiente_1_400(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    _, status = await _post_xml(test_client, token, _clave(15), ambiente=1)
    assert status == 400


@pytest.mark.asyncio
async def test_confirmar_xml_rol_lectura_403(test_client: AsyncClient) -> None:
    admin_token = await _admin_token(test_client)
    lectura_token = await _create_user_token(
        test_client, admin_token, "lectura_xml_confirmar@test.com", "lectura"
    )
    _, status = await _post_xml(test_client, lectura_token, _clave(16))
    assert status == 403


# =============================================================
# Listar tests
# =============================================================


@pytest.mark.asyncio
async def test_listar_xmls_paginado_200(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    for i in range(20, 25):
        await _post_xml(test_client, token, _clave(i))

    resp = await test_client.get(
        "/xmls?page=1&page_size=3",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 5
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_listar_xmls_excluye_inactivos(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(30))
    xml_id = uuid.UUID(data["id"])

    usuario_result = await db_session.execute(
        select(Usuario.id).where(Usuario.email == "admin@sistema.com")
    )
    usuario_id = usuario_result.scalar_one()

    xml_result = await db_session.execute(select(Xml).where(Xml.id == xml_id))
    xml = xml_result.scalar_one()
    xml.soft_delete(usuario_id)
    await db_session.flush()

    resp = await test_client.get("/xmls", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    ids_in_list = [item["id"] for item in resp.json()["items"]]
    assert str(xml_id) not in ids_in_list


# =============================================================
# Detalle tests
# =============================================================


@pytest.mark.asyncio
async def test_detalle_xml_existente_200(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    created, _ = await _post_xml(test_client, token, _clave(40))
    xml_id = created["id"]

    resp = await test_client.get(
        f"/xmls/{xml_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == xml_id
    assert "clave_acceso" in data
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_detalle_xml_inexistente_404(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    fake_id = uuid.uuid4()
    resp = await test_client.get(
        f"/xmls/{fake_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


# =============================================================
# Pendientes tests
# =============================================================


@pytest.mark.asyncio
async def test_pendientes_xml_parcialmente_ingresado(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(50), two_items=True)
    xml_id = data["id"]
    items = data["items"]
    assert len(items) == 2

    # Zero out the first item — only the second should remain pending
    first_item_id = uuid.UUID(items[0]["id"])
    await db_session.execute(
        update(XmlItem)
        .where(XmlItem.id == first_item_id)
        .values(cantidad_pendiente=Decimal("0"))
    )
    await db_session.flush()

    resp = await test_client.get(
        f"/xmls/{xml_id}/pendientes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    pendientes = resp.json()
    assert len(pendientes) == 1
    assert pendientes[0]["id"] == items[1]["id"]


@pytest.mark.asyncio
async def test_pendientes_xml_totalmente_ingresado(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _admin_token(test_client)
    data, _ = await _post_xml(test_client, token, _clave(51))
    xml_id = data["id"]

    await db_session.execute(
        update(XmlItem)
        .where(XmlItem.xml_id == uuid.UUID(xml_id))
        .values(cantidad_pendiente=Decimal("0"))
    )
    await db_session.flush()

    resp = await test_client.get(
        f"/xmls/{xml_id}/pendientes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_pendientes_rol_lectura_403(test_client: AsyncClient) -> None:
    admin_token = await _admin_token(test_client)
    lectura_token = await _create_user_token(
        test_client, admin_token, "lectura_xml_pendientes@test.com", "lectura"
    )
    data, _ = await _post_xml(test_client, admin_token, _clave(60))
    xml_id = data["id"]

    resp = await test_client.get(
        f"/xmls/{xml_id}/pendientes",
        headers={"Authorization": f"Bearer {lectura_token}"},
    )
    assert resp.status_code == 403
