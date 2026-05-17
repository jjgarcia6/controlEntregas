"""Unit tests for xml_parser_service — no DB required."""
from decimal import Decimal

import pytest

from app.services import xml_parser_service
from app.utils.exceptions import ValidacionNegocio

_CLAVE = "1234567890123456789012345678901234567890123456789"  # 49 chars


def _build_xml(
    *,
    ambiente: int = 2,
    tarifa: str = "15",
    peso_valor: str | None = "10.0",
    cantidad: str = "4.0",
    version: str = "2.1.0",
    root_tag: str = "factura",
) -> str:
    peso_bloque = (
        f'<detallesAdicionales><detAdicional nombre="Peso" valor="{peso_valor}"/></detallesAdicionales>'
        if peso_valor is not None
        else ""
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<{root_tag} version="{version}" id="comprobante">
  <infoTributaria>
    <ambiente>{ambiente}</ambiente>
    <tipoEmision>1</tipoEmision>
    <razonSocial>EMPRESA TEST SA</razonSocial>
    <ruc>1790012345001</ruc>
    <claveAcceso>{_CLAVE}</claveAcceso>
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
      <codigoPrincipal>PROD001</codigoPrincipal>
      <descripcion>Producto de prueba</descripcion>
      <cantidad>{cantidad}</cantidad>
      <precioUnitario>25.00</precioUnitario>
      <descuento>0.00</descuento>
      <precioTotalSinImpuesto>100.00</precioTotalSinImpuesto>
      {peso_bloque}
      <impuestos>
        <impuesto>
          <codigo>2</codigo>
          <codigoPorcentaje>4</codigoPorcentaje>
          <tarifa>{tarifa}</tarifa>
          <baseImponible>100.00</baseImponible>
          <valor>15.00</valor>
        </impuesto>
      </impuestos>
    </detalle>
  </detalles>
</{root_tag}>"""


def test_parsear_xml_sri_valido_ambiente_2() -> None:
    result = xml_parser_service.parsear(_build_xml())

    assert result.clave_acceso == _CLAVE
    assert result.ruc_emisor == "1790012345001"
    assert result.razon_social_emisor == "EMPRESA TEST SA"
    assert result.numero_factura == "001-001-000000001"
    assert result.ambiente == 2
    assert result.ruc_comprador == "0912345678001"
    assert result.importe_total == Decimal("115.00")
    assert len(result.items) == 1
    assert result.xml_raw.startswith("<?xml")


def test_parsear_xml_ambiente_1_lanza_excepcion() -> None:
    with pytest.raises(ValidacionNegocio, match="ambiente de producción"):
        xml_parser_service.parsear(_build_xml(ambiente=1))


def test_parsear_xml_no_es_factura_sri() -> None:
    xml = _build_xml(root_tag="nota")
    with pytest.raises(ValidacionNegocio, match="factura SRI 2.x"):
        xml_parser_service.parsear(xml)


def test_parsear_xml_mal_formado() -> None:
    with pytest.raises(ValidacionNegocio, match="XML válido"):
        xml_parser_service.parsear("<esto no es xml valido >>>")


def test_peso_unitario_calculado_con_detAdicional() -> None:
    result = xml_parser_service.parsear(_build_xml(peso_valor="10.0", cantidad="4.0"))
    item = result.items[0]

    assert item.peso_documento == Decimal("10.0")
    assert item.peso_unitario == Decimal("2.5")


def test_peso_unitario_cero_sin_detAdicional() -> None:
    result = xml_parser_service.parsear(_build_xml(peso_valor=None))
    item = result.items[0]

    assert item.peso_documento == Decimal("0")
    assert item.peso_unitario == Decimal("0")


def test_tarifa_iva_extraida_del_xml_15() -> None:
    result = xml_parser_service.parsear(_build_xml(tarifa="15"))
    item = result.items[0]

    assert item.tarifa_iva == Decimal("15")


def test_tarifa_iva_extraida_del_xml_0() -> None:
    result = xml_parser_service.parsear(_build_xml(tarifa="0"))
    item = result.items[0]

    assert item.tarifa_iva == Decimal("0")
